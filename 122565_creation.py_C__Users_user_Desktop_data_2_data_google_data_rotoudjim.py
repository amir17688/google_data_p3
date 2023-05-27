import sys
import time

from django.conf import settings
from django.db.utils import load_backend
from django.db.backends import creation

# The prefix to put on the default database name when creating
# the test database.
TEST_DATABASE_PREFIX = 'test_'


class BaseDatabaseCreation(creation.BaseDatabaseCreation): pass