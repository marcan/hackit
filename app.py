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

import random, os, os.path
from flask import Flask, request, session, g, render_template, flash, redirect, url_for
from wtforms import Form, BooleanField, TextField, PasswordField, validators
import sqlalchemy.exc

import users
import level
from ranking import get_ranking

# ====== Init ======

app = Flask(__name__)
app.config.from_object("config")
users.db.init_app(app)

import logging

class RequestFormatter(logging.Formatter):
    def format(self, record):
        s = logging.Formatter.format(self, record)
        try:
            return '[%s] [%s] [%s %s] '%(self.formatTime(record), request.remote_addr, request.method, request.path) + s
        except:
            return '[%s] [SYS] '%self.formatTime(record) + s

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('127.0.0.1',
                                app.config['ADMIN_EMAIL'],
                                app.config['ADMIN_EMAIL'], 'Hack It ERROR')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    handler = logging.FileHandler(os.path.join(app.root_path, app.config['LOG_FILE']))
    handler.setLevel(logging.INFO)
    handler.setFormatter(RequestFormatter())
    app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
    app.logger.warning('Starting...')

# ====== Simple pages ======

@app.route('/')
def index():
    return render_template('intro.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/about')
def about():
    authors = set()
    for r in level.routes:
        for l in r.levels:
            if isinstance(l.author, list) or isinstance(l.author, tuple):
                for i in l.author:
                    authors.add(i)
            else:
                authors.add(l.author)
    authors = list(authors)
    random.shuffle(authors)
    return render_template('about.html', authors=authors)

@app.route('/ranking')
def ranking():
    grank, rrank = get_ranking(app.config)
    rrank = zip(level.routes, rrank)
    return render_template('ranking.html', grank=grank, rrank=rrank)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('notfound.html'), 404

# ====== User management ======

class BaseProfileForm(Form):
    password2 = PasswordField(u'Repite la contraseña')
    pubname = TextField(u'Nombre público', [validators.Length(min=1, max=30,
        message=u'El nombre debe tener entre 1 y 30 caracteres')])
    email = TextField(u'Email', [
        validators.Email(message=u'Email no válido'),
        validators.Length(max=60, message=u'La longitud máxima del e-mail es de 60 caracteres')
    ])
    if app.config['USE_SEAT']:
        seat = TextField(u'Puesto en la party', [validators.Length(min=3, max=30,
            message=u'El puesto debe tener entre 3 y 30 caracteres')])

class ProfileForm(BaseProfileForm):
    username = TextField(u'Nombre de usuario', [validators.Optional()])
    password = PasswordField(u'Contraseña', [
        validators.Optional(),
        validators.EqualTo('password2', message=u'Las contraseñas no coinciden'),
        validators.Length(min=6, message=u'La contraseña debe tener como mínimo 6 caracteres')
    ])

class RegistrationForm(BaseProfileForm):
    username = TextField(u'Nombre de usuario', [validators.Length(min=2, max=30,
        message=u'El nombre de usuario debe tener entre 2 y 30 caracteres')])
    password = PasswordField(u'Contraseña', [
        validators.Required(message=u'Debes introducir una contraseña'),
        validators.EqualTo('password2', message=u'Las contraseñas no coinciden'),
        validators.Length(min=6, message=u'La contraseña debe tener como mínimo 6 caracteres')
    ])
    accept_rules = BooleanField(u'He leído y acepto las bases', [
        validators.Required(message=u'Debes aceptar las bases')])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user is not None:
        return redirect(url_for('index'))

    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
        if form.username.data in app.config['BANNED_USERNAMES']:
            form.username.errors.append(u'Buen intento ;)')
            return render_template('register.html', form=form)
        if app.config['USE_SEAT']:
            seat = form.seat.data
        else:
            seat = None
        newuser = users.User(form.username.data, form.password.data,
            form.pubname.data, form.email.data, seat)
        try:
            users.db.session.add(newuser)
            users.db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            form.username.errors.append(u'Ya existe un usuario con ese nombre')
        else:
            flash(u'Te has registrado con éxito. ¡Comienza el desafío!')
            session['user_id'] = newuser.id
            g.user = newuser
            app.logger.info('[%s] Registered %r,%r,%r', g.user, g.user.pubname, g.user.email, g.user.seat)
            return level.autosolve(app) or redirect(url_for('index'))

    return render_template('register.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if g.user is None:
        return redirect(url_for('index'))

    form = ProfileForm(request.form)
    form.username.data = g.user.username

    if request.method == 'POST' and form.validate():
        g.user.pubname = form.pubname.data
        g.user.email = form.email.data
        if app.config['USE_SEAT']:
            g.user.seat = form.seat.data

        if form.password.data:
            g.user.changepassword(form.password.data)

        users.db.session.commit()
        app.logger.info('[%s] profile updated %r,%r,%r', g.user, g.user.pubname, g.user.email, g.user.seat)
        flash(u'Perfil actualizado correctamente')
    else:
        form.pubname.data = g.user.pubname
        form.email.data = g.user.email
        if app.config['USE_SEAT']:
            form.seat.data = g.user.seat

    return render_template('profile.html', form=form)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    app.logger.warning('[%s] account deleted', g.user)
    users.db.session.delete(g.user)
    users.db.session.commit()
    del session['user_id']
    session['csrf_token'] = os.urandom(8).encode('hex')
    flash(u'Cuenta de usuario borrada')
    return redirect(url_for('index'))

class LoginForm(Form):
    username = TextField(u'Nombre de usuario')
    password = PasswordField(u'Contraseña')

@app.route('/login', methods=['POST'])
def login():
    if g.user is not None:
        return redirect(url_for('index'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        user = users.User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash(u'El usuario no existe')
        elif not user.checkpassword(form.password.data):
            flash(u'Contraseña incorrecta')
            app.logger.info('[%s] login failed', user)
        else:
            flash(u'Bienvenido de nuevo, %s'%user.username)
            session['user_id'] = user.id
            g.user = user
            app.logger.info('[%s] login succeeded', user)
            return level.autosolve(app) or redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session['csrf_token'] = os.urandom(8).encode('hex')
    if 'user_id' in session:
        del session['user_id']
        flash(u'Has cerrado tu sesión')
    return redirect(url_for('index'))

# ====== Levels ======

for r in level.routes:
    for l in r.levels:
        app.register_blueprint(l, url_prefix='/%s/%d'%(r.name, l.number))
        l.config = app.config
        l.logger = app.logger

# ====== Global request processing ======

@app.before_request
def setup_tasks():
    if request.method == 'POST':
        if ('csrf_token' not in session or (
            ('csrf_token' not in request.form or
                request.form['csrf_token'] != session['csrf_token'])
            and ('X-CSRF' not in request.headers or
                 request.headers['X-CSRF'] != session['csrf_token']))):
            flash(u'Error de token CSRF')
            return redirect(url_for('index'))

    if 'csrf_token' not in session:
        session['csrf_token'] = os.urandom(8).encode('hex')

    g.user = None

    if 'user_id' in session and not request.path.startswith('/static/'):
        g.user = users.User.query.filter_by(id=session['user_id']).first()
        if g.user is None:
            del session['user_id']

    g.sb_routes = []
    for r in level.routes:
        lv = []
        for l in r.levels:
            lv.append(l)
        g.sb_routes.append((r, lv))

# ====== Built-in server ======

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'createdb':
            app.test_request_context().push()
            users.db.create_all()
            sys.exit(0)
    app.run()
