# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from dev_settings import *

INSTALLED_APPS += (
    'django_nose',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

CACHE_PREFIX = "testcache"
CACHE_TIMEOUT = 60
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_PLUGINS = ['utils.test_utils.UnisubsTestPlugin']
CELERY_ALWAYS_EAGER = True

YOUTUBE_CLIENT_ID = 'test-youtube-id'
YOUTUBE_CLIENT_SECRET = 'test-youtube-secret'
YOUTUBE_API_KEY = 'test-youtube-api-key'

# Use MD5 password hashing, other algorithms are purposefully slow to increase
# security.  Also include the SHA1 hasher since some of the tests use it.
PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
        'django.contrib.auth.hashers.SHA1PasswordHasher',
)

# Let the nose CaptureLogging plugin handle logging.  It doesn't display
# logging at all, except if there's a test failure.
del LOGGING

NOSE_ARGS = ['--logging-filter=test_steps, -remote_connection, '
             '-selenium.webdriver.remote.remote_connection',
             '--with-xunit', '--logging-level=ERROR',
             '--xunit-file=nosetests.xml',
            ]

try:
    from dev_settings_test_local import *
except ImportError:
    pass
