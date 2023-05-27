from __future__ import absolute_import
from attest import Tests
from . import transaction, unit


tests = Tests()
tests.register(transaction.tests)
tests.register(unit.tests)

