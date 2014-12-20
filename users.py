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

try:
    from flaskext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm.collections import column_mapped_collection

from datetime import datetime

from passlib.hash import pbkdf2_sha256

db = SQLAlchemy()

class LevelState(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    level = db.Column(db.String(32), primary_key=True)
    route = db.Column(db.String(32), nullable=False)
    state = db.Column(db.Enum('unsolved','skipped','solved', name="LEVELSTATE"))
    password = db.Column(db.String(128))
    description = db.Column(db.String(2048))
    timestamp = db.Column(db.DateTime())

    def __init__(self, level, state='unsolved', password=None, description=None):
        self.level = level.name
        self.route = level.route_.name
        self.state = state
        self.password = password
        self.description = description
        self.timestamp = datetime.utcnow()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    pubname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(60), nullable=False)
    seat = db.Column(db.String(30))

    levels = db.relation(LevelState, cascade='all, delete, delete-orphan',
                collection_class=column_mapped_collection(LevelState.level))

    def __init__(self, username, password, pubname, email, seat=None):
        self.username = username
        self.password = pbkdf2_sha256.encrypt(password)
        self.pubname = pubname
        self.email = email
        self.seat = seat

    def checkpassword(self, pwd):
        return pbkdf2_sha256.verify(pwd, self.password)

    def changepassword(self, pwd):
        self.password = pbkdf2_sha256.encrypt(pwd)

    def getstate(self, level):
        if level.name in self.levels:
            return self.levels[level.name]
        else:
            return LevelState(level, 'unsolved')

    def setstate(self, level, state, password=None, description=None):
        if level.name in self.levels:
            ls = self.levels[level.name]
            ls.state = state
            ls.password = password
            ls.description = description
            ls.timestamp = datetime.utcnow()
        else:
            state = LevelState(level, state, password, description)
            self.levels[level.name] = state

    def lock(self):
        db.session.refresh(self, lockmode='update')

    def unlock(self):
        db.session.rollback()

    def commit(self):
        db.session.commit()

    def __repr__(self):
        return '<User #%d %r>' % (self.id, self.username)
    def __str__(self):
        return '(%d)%s' % (self.id, self.username)

