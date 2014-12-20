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

import os.path, runpy
from datetime import datetime

from flask import Blueprint, request, session, g, render_template, redirect, flash, url_for, make_response
from jinja2 import FileSystemLoader
from werkzeug import cached_property

from levels import routes as _routes
from ranking import get_solvers

app_root = os.path.abspath(os.path.dirname(__file__))
levels_root = os.path.join(app_root, 'levels')
app_templates = os.path.join(app_root, 'templates')

class Level(Blueprint):
    LEVEL_GLOBALS = ['request', 'session', 'g', 'make_response', 'flash', 'redirect', 'url_for']
    LEVEL_ITEMS = ['title', 'author', 'password', 'index', 'case_sensitive']

    def __init__(self, name, route, idx):
        root_path = os.path.join(levels_root, name)
        Blueprint.__init__(self, name, import_name=__name__,
        static_folder=os.path.join(root_path, 'static'),
        template_folder=levels_root)
        self.root_path = root_path
        self.name = name
        self.route_ = route
        self.routeidx = idx
        self.number = idx + 1
        self.root_path = os.path.join(levels_root, name)
        gbls = dict([(i,globals()[i]) for i in self.LEVEL_GLOBALS])
        gbls['level'] = self
        def _render_template(name, **context):
            context['level'] = self
            context['route'] = self.route_
            context['solvers'] = get_solvers(self.config, self)
            return render_template('%s/%s'%(self.name, name), **context)
        gbls['render_template'] = _render_template
        gbls['case_sensitive'] = None
        self.level = runpy.run_module('levels.%s.level' % name, gbls)
        for i in self.LEVEL_ITEMS:
            if i in self.level:
                self.__dict__[i] = self.level[i]
        if isinstance(self.author, list) or isinstance(self.author, tuple):
            self.author_text = ' & '.join(self.author)
        else:
            self.author_text = self.author
        if 'index' not in self.level:
            @self.route('/')
            def index():
                return _render_template('index.html')
            self.index = index

        @self.route('/solve', methods=['POST'])
        def solve():
            password = None
            if 'password' in request.form:
                password = request.form['password']
            return self.solve(password)

        @self.route('/skip', methods=['POST'])
        def skip():
            return self.skip()

        @self.before_request
        def check_perms():
            if self.state() == 'closed':
                self.logger.warning('[%s][%s] level forbidden', g.user, self.name)
                return render_template('forbidden.html'), 403

    def checkpassword(self, password):
        case_sensitive = self.case_sensitive
        if case_sensitive is None:
            case_sensitive = self.config['CASE_SENSITIVE']
        if isinstance(self.password, str) or isinstance(self.password, unicode):
            if case_sensitive:
                return password == self.password
            else:
                return password.lower() == self.password.lower()
        elif isinstance(self.password, list) or isinstance(self.password, tuple):
            if case_sensitive:
                return password in self.password
            else:
                return password.lower() in (p.lower() for p in self.password)
        elif hasattr(self.password, '__call__'):
            return self.password(password)
        else:
            raise TypeError("Invalid password object")

    def solve(self, password, auto=False):
        state = self.state()
        if state == 'solved':
            self.logger.info('[%s][%s] solve while already solved', g.user, self.name)
            return redirect(url_for(self.name + '.index'))
        elif state not in ('open', 'skipped'):
            self.logger.warning('[%s][%s] solve while in invalid state', g.user, self.name)
            return render_template('forbidden.html'), 403

        if not self.checkpassword(password):
            self.logger.info('[%s][%s] bad password %r', g.user, self.name, password)
            flash(u"¡Contraseña incorrecta! Inténtalo de nuevo.")
            return redirect(url_for(self.name + '.index'))

        if g.user is None:
            self.logger.info('[%s][%s] anonymous solve %r', g.user, self.name, password)
            if 'autosolve' not in session:
                session['autosolve'] = []
            for name, routeidx, p in session['autosolve']:
                if name == self.route_.name and routeidx == self.routeidx:
                    break
            else:
                session['autosolve'].append((self.route_.name, self.routeidx, password))
            return render_template('anonsolved.html', level=self)

        description = None
        if self.config['REQUIRE_DESCRIPTION'] and self.routeidx != 0:
            if 'description' not in request.form:
                return render_template('solved.html', level=self, password=password)
            else:
                description = request.form['description'][:2000]

        g.user.lock()
        state = self.state()
        if state == 'solved':
            g.user.unlock()
            self.logger.warning('[%s][%s] solve() while already solved (locked)', g.user, self.name)
            return redirect(url_for(self.name + '.index'))
        elif state not in ('open', 'skipped'):
            self.logger.warning('[%s][%s] solve() while in invalid state (locked)', g.user, self.name)
            return render_template('forbidden.html'), 403

        g.user.setstate(self, 'solved', password, description)
        g.user.commit()
        self.logger.info('[%s][%s] solved with password %r', g.user, self.name, password)

        if not auto:
            flash(u"¡Bien hecho, has superado el nivel %d!" % self.number)
        try:
            next = self.route_.levels[self.routeidx+1]
            return redirect(url_for(next.name + '.index'))
        except IndexError:
            alldone = all([l.state() == 'solved' for r in routes for l in r.levels])
            self.logger.info('[%s][%s] last level (alldone=%r)', g.user, self.name, alldone)
            return render_template('alldone.html', alldone=alldone, level=self)

    def skip(self):
        if g.user is None:
            self.logger.info('[%s][%s] anonymous skip', g.user, self.name)
            return redirect(url_for(self.name + '.index'))

        g.user.lock()
        if not self.can_skip():
            g.user.unlock()
            self.logger.warning('[%s][%s] skip() but can\'t skip', g.user, self.name)
            return render_template('forbidden.html'), 403

        g.user.setstate(self, 'skipped')
        g.user.commit()
        self.logger.info('[%s][%s] skipped', g.user, self.name)

        flash(u"Te has saltado el nivel %d" % self.number)
        try:
            next = self.route_.levels[self.routeidx+1]
            return redirect(url_for(next.name + '.index'))
        except IndexError:
            alldone = all([l.state() == 'solved' for r in routes for l in r.levels])
            self.logger.info('[%s][%s] last level (alldone=%r)', g.user, self.name, alldone)
            return render_template('alldone.html', alldone=alldone, level=self)

    def can_skip(self):
        if g.user is None:
            return False

        if self.state() == 'skipped':
            return False

        skipped = 0
        for k,v in g.user.levels.items():
            if v.state == 'skipped':
                skipped += 1

        if skipped > self.config['MAX_SKIP']:
            self.logger.error('[%s][%s] User has %d skips, but max %d', skipped, self.config['MAX_SKIP'])
            return False
        elif skipped == self.config['MAX_SKIP']:
            return False
        else:
            return True

    def state(self):
        if datetime.utcnow() < self.config['START_TIME']:
            return 'closed'

        if g.user is None:
            if self.routeidx == 0:
                return 'open'
            else:
                return 'closed'
        else:
            userstate = g.user.getstate(self).state
            if userstate == 'unsolved':
                if self.routeidx == 0:
                    return 'open'
                for prev in self.route_.levels[:self.routeidx]:
                    prevstate = g.user.getstate(prev).state
                    if prevstate not in ('solved','skipped'):
                        return 'closed'
                else:
                    return 'open'
            else:
                return userstate

    def solved_password(self):
        if g.user is None:
            return None
        elif self.state() == 'solved':
            return g.user.getstate(self).password
        else:
            return None

    #@cached_property
    #def jinja_loader(self):
        #return FileSystemLoader([levels_root, app_templates])

    def __str__(self):
        return "<Level %d.%s '%s'>"%(self.number, self.name, self.title)

class Route(object):
    def __init__(self, name):
        self.name = name
        self.title = _routes.route_titles[name]
        self.levels = []
        for i,j in enumerate(_routes.route_levels[name]):
            self.levels.append(Level(j, self, i))
    def __str__(self):
        return "<Route %s '%s': %d levels>"%(self.name, self.title, len(self.levels))

routes = [Route(name) for name in _routes.routes]

routes_by_name = dict([(r.name, r) for r in routes])

def autosolve(app):
    if 'autosolve' not in session:
        return None
    if g.user is None:
        return None

    last_res = None
    try:
        for name, idx, password in session['autosolve']:
            app.logger.info('[%s] autosolve %r, %r, %r', g.user, name, idx, password)
            level = routes_by_name[name].levels[idx]
            res = level.solve(password, auto=True)
            if res is not None:
                last_res = res
    except:
        app.logger.exception('[%s] autosolve failed: (%r)', g.user, session['autosolve'])

    del session['autosolve']
    return last_res

if __name__ == '__main__':
    for route in routes:
        print route
        for level in route.levels:
            print level
