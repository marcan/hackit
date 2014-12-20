from datetime import datetime

# Enables a live web debugger for Python exceptions.
# Make sure to turn this off in production! This is a gaping security hole!
DEBUG = True

# Log file (only used in production, if DEBUG is False). This must be writable
# by the process that the framework runs as. It defaults to a directory
# relative to the framework root, but may be set to an absolute path.
LOG_FILE = 'log/info.log'

# Make sure to change this to a secure key in production!
SECRET_KEY = 'changeme_dummy'

# SQLite is not supported in production - please use PostgreSQL. The locking
# semantics have only been verified with PostgreSQL - don't come crying if
# you use MySQL and someone pulls a race condition attack against your
# instance and skips too many levels at once. SQLite is OK for development.
SQLALCHEMY_DATABASE_URI = 'sqlite:///hackit.db'
#SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2:///hackit?host=/tmp'
# Turn this off in production.
SQLALCHEMY_ECHO = True

# How many prizes to allocate to teams from the combined list of all routes.
GLOBAL_PRIZES = 1
# How many prizes to allocate individually to teams from each route, after
# global winners are excluded.
ROUTE_PRIZES = 2

# No levels are open before the start time. Note: this is UTC, not local time!
START_TIME = datetime(2001, 1, 1, 0, 0)
# Levels may still be solved after the end time, but such solutions do not
# count towards the ranking. Also UTC.
END_TIME = datetime(2099, 1, 1, 0, 0)

# The main title displayed in a large font on the template.
SITE_MAINTITLE = 'Fail It'
# The subtitle displayed in a smaller font.
SITE_SUBTITLE = str(datetime.utcnow().year)
# The combined title used for the <title> element and other misc locations.
SITE_NAME = SITE_MAINTITLE + ' ' + SITE_SUBTITLE

EVENT_NAME = 'Fail Party'

# How many levels may be skipped by a user at any given time.
MAX_SKIP = 2
# Whether solving levels beyond the first in each route requires the user to
# fill in a write-up or description of how they solved it.
REQUIRE_DESCRIPTION = True

# Usernames that may not be registered. There is no significance within the
# framework, but specific levels may assign meaning to login usernames. Note
# that there are currently no restrictions on username character sets and,
# indeed, unicode, spaces, and control characters are allowed (and will only
# serve to annoy the user in question, really, since it'll just make login more
# difficult). This may change in the future.
BANNED_USERNAMES = ('root',)

# Whether the registration process requires providing a seat location.
# Undocumented hack: setting your seat to "Control" hides you from the ranking
# list and lists of users who have completed each level, useful for admin
# testing without disturbing the competition.
USE_SEAT = True

# The default case sensitivity for passwords, if not provided in level.py.
CASE_SENSITIVE = True

# Nickname or real name of the site admin.
ADMIN_NAME = 'lamerazo'
# E-mail address of the site admin.
ADMIN_EMAIL = 'lamerazo@example.com'
# Web address of the site admin.
ADMIN_WWW = 'http://example.com'
