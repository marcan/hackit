#!/usr/bin/python2
# -!- coding: utf-8 -!-

# Copyright 2010-2014 Hector Martin "marcan" <marcan@marcan.st>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import level
from users import User, LevelState, db

from sqlalchemy import or_

class Score(object):
    def __init__(self, user, score, timestamp):
        self.user = user
        self.score = score
        self.timestamp = timestamp

    def __cmp__(self, other):
        return cmp(self.score, other.score) or cmp(other.timestamp, self.timestamp)

    def __repr__(self):
        return '<Score %s: %r, %r>'%(self.user, self.score, self.timestamp)

def merge(*lists):
    combined = {}
    for l in lists:
        for score in l:
            if score.user in combined:
                combined[score.user].score += score.score
                combined[score.user].timestamp = max(combined[score.user].timestamp, score.timestamp)
            else:
                combined[score.user] = Score(score.user, score.score, score.timestamp)
    return sorted(combined.values(), reverse=True)

def remove(list, user):
    for i in list:
        if i.user == user:
            list.remove(i)

def rank(routes, config):
    routes_orig = [sorted(list(r), reverse=True) for r in routes]
    routes = map(list, routes_orig)
    combined = merge(*routes)

    global_prizes = [i.user for i in combined[:config['GLOBAL_PRIZES']]]

    for user in global_prizes:
        for l in routes:
            remove(l, user)

    for r in routes:
        r.sort(reverse=True)

    route_prizes = [[] for i in range(len(routes))]

    for prize in range(config['ROUTE_PRIZES']):
        tier = [None]*len(routes)
        while not all(tier):
            for ri in range(len(routes)):
                if tier[ri] is None:
                    if len(routes[ri]) == 0:
                        tier[ri] = -1
                    else:
                        tier[ri] = routes[ri][0].user
                        routes[ri] = routes[ri][1:]
            for user in tier:
                if user == -1:
                    continue
                slots = [i for i,t in enumerate(tier) if t == user]
                if len(slots) > 1:
                    lowest = 0
                    for s in slots:
                        if len(routes[s]) == 0:
                            lowest = s
                            break
                        if routes[lowest][0] > routes[s][0]:
                            lowest = s
                    for s in slots:
                        if s != lowest:
                            tier[s] = None

        for user in tier:
            for l in routes:
                remove(l, user)

        for i,user in enumerate(tier):
            if user != -1:
                route_prizes[i].append(user)

    return combined, routes_orig, global_prizes, route_prizes

def map_ranking(offset, l, prizes):
    rank = []
    for i in l:
        if i.user in prizes:
            rank.append((prizes.index(i.user) + offset, i))
        else:
            rank.append((None, i))
    return rank

def get_ranking(config):
    routes = []
    session = db.session

    for r in level.routes:
        rl = []
        for user, levels, timestamp in \
                session.query(User, db.func.count(LevelState.level),db.func.max(LevelState.timestamp)).\
                join(LevelState).\
                filter(LevelState.route==r.name).\
                filter(LevelState.timestamp < config['END_TIME']).\
                filter(LevelState.state=='solved').\
                filter(or_(User.seat == None, User.seat != 'Control')).\
                group_by(User):
            rl.append(Score(user, levels, timestamp))
        routes.append(rl)

    combined, routes, global_prizes, route_prizes = rank(routes, config)

    grank = map_ranking(1, combined, global_prizes)
    rrank = [map_ranking(1 + config['GLOBAL_PRIZES'], routes[i], route_prizes[i]) for i in range(len(routes))]

    return grank, rrank

def get_solvers(config, level):
    solvers = []
    for user in \
        db.session.query(User).\
        join(LevelState).\
        filter(LevelState.route==level.route_.name).\
        filter(LevelState.level==level.name).\
        filter(LevelState.timestamp < config['END_TIME']).\
        filter(LevelState.state=='solved').\
        filter(or_(User.seat == None, User.seat != 'Control')).\
        group_by(User):
        solvers.append(user.pubname)
    return solvers

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object("config")
    db.init_app(app)
    app.test_request_context().push()

    grank, rrank = get_ranking(app.config)
    print "Global Ranking:"
    for prize, score in grank:
        if prize is not None:
            print "[%d] %s"%(prize, score.user.pubname)
        else:
            print "[ ] %s"%(score.user.pubname)

    for i,r in enumerate(rrank):
        print "%s Ranking:"%level.routes[i].title
        for prize, score in r:
            if prize is not None:
                print "[%d] %s (%d, %r)"%(prize, score.user.pubname, score.score, score.timestamp)
            else:
                print "[ ] %s (%d, %r)"%(score.user.pubname, score.score, score.timestamp)
