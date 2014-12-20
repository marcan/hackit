Hack It Framework
=================

Hack It Framework is the framework behind the Hack It and Solve It competitions
at Euskal Encounter, Gipuzkoa Encounter, and Araba Encounter.

Installation
------------

Hack It Framework is built using Python 2 and Flask, with SQLAlchemy, WTForms,
and passlib. PostgreSQL and flup are also needed when running in production.

On Gentoo Linux, you need the following dependencies to run the application in
development mode:
* dev-python/flask
* dev-python/flask-sqlalchemy
* dev-python/flask-wtf
* dev-python/passlib

To run it in production mode, you'll need these too:
* dev-db/postgresql-base
* dev-db/postgresql-server
* dev-python/psycopg
* dev-python/flup

To run the app in development mode, install all required dependencies and then
run:
```sh
$ python2 app.py createdb
$ python2 app.py
```

This will create an empty SQLite database named `hackit.db` and start listening
on [localhost:5000](http://localhost:5000). You will see debug info printed to
your terminal as you access the site.

To run the app in production mode, create a suitable config.py (make sure you
follow the guidelines mentioned in the comments in the example config). You'll
need a FastCGI web server and process manager (nginx and spawn-fcgi are
recommended). Point your process manager at the [hackit.fcgi](hackit.fcgi)
executable. Before running the server, create the database by running
`python2 app.py createdb` as the same user that the server will run as.

Building levels
---------------

Levels are held in subfolders of the [levels](levels/) folder, and referenced by
[routes.py](levels/routes.py). There are two example levels provided, a simple
one and a more complex one. Levels are really just syntactic sugar for
Flask [Blueprints](http://flask.pocoo.org/docs/0.10/blueprints/#blueprints) with
a bunch of globals pre-seeded into the module namespace, together with a
Jinja2 template, so you can use pretty much any Flask feature (and you can
import additional modules).

i18n
----

Currently the UI is largely in Spanish (no i18n support is present), so you will
have to translate all the strings manually if you want to use the framework in
another language. Pull requests to add proper i18n support are welcome (in
particular for strings hardcoded in .py files; HTML templates should be easy
to deal with by just having language-specific child templates). The goal would
be to have the default/core language be English with a Spanish i18n resource
file, in that case.

License
-------

Copyright 2010-2014 Hector Martin "marcan" (<marcan@marcan.st>)  
Copyright 2010 Freddy Leitner "Digital Dreamer" (<http://www.dreamer.de>)  

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this software except in compliance with the License.
You may obtain a copy of the License at

* http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


