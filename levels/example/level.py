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

# The title used for the level (in the sidebar and in the main level page)
title = u'Ejemplo'

# The author of the level (displayed as a subtitle and also aggregated in the About page)
author = u'marcan'

# Whether the password is case sensitive (does not apply for custom functions).
# Defaults to the value of CASE_SENSITIVE in config.py.
case_sensitive = True

# The password for the level
password = u'Ex4mpl3'

# Multiple valid passwords:
#password = (u'Example', u'Ejemplo')

# Custom password verification functions:
# Accept any password (!)
#password = lambda x: True

# Accept any password of length 42
#password = lambda x: len(x) == 42

# Accept any password where the ASCII values of the characters sum up to 1337
#def password(x):
#    acc = 0
#    for c in x:
#        acc += chr(x)
#    return acc == 1337

# Only title, author, password are required. However, you can add arbitrary
# Python code including additional handlers or override the main level page
# handler altogether.

# A custom handler (to be used by, say, a Javascript XHR)
@level.route('/stupidcheck')
def stupidcheck():
    p = request.args.get('password', '')
    if len(p) != len(password):
        return "Wrong length!"
    for i, (a, b) in enumerate(zip(p, password)):
        if a != b:
            return "Wrong char at %d!" % i
    return "W00t!"

# Normal Flask/WSGI rules for responses apply
@level.route('/special_page')
def fail404():
    return make_response("Nothing to see here, please move along.", 404)

# Override the main level page
import sys
@level.route('/')
def index():
    return render_template('index.html', version=sys.version)
