from attest import assert_hook, Tests
from werkzeug.contrib.cache import BaseCache
from flask_volatile.transaction import Transaction


tests = Tests()


class TestCache(BaseCache):

    def __init__(self, plan={}, *args, **kwargs):
        super(BaseCache, self).__init__(*args, **kwargs)
        self.cache = {}
        self.counter = 0
        self.plan = plan

    def inject_op(self):
        try:
            op = self.plan[self.counter]
        except KeyError:
            pass
        else:
            self.counter += 1
            if callable(op):
                op(self)
            else:
                method = op[0]
                getattr(self, method)(*op[1:])

    def get(self, key):
        self.inject_op()
        result = self.cache.get(key)
        self.counter += 1
        self.inject_op()
        return result

    def set(self, key, value, timeout=None):
        self.inject_op()
        self.cache[key] = value
        self.counter += 1
        self.inject_op()

    def add(self, key, value, timeout=None):
        self.inject_op()
        if key not in self.cache:
            self.cache[key] = value
        self.counter += 1
        self.inject_op()

    def delete(self, key):
        self.inject_op()
        del self.cache[key]
        self.counter += 1
        self.inject_op()

    def inc(self, key, delta=1):
        self.inject_op()
        self.cache[key] = self.cache.setdefault(key, 0) + delta
        self.counter += 1
        self.inject_op()

    def dec(self, key, delta=1):
        self.inject_op()
        self.cache[key] = self.cache.setdefault(key, 0) - delta
        self.counter += 1
        self.inject_op()


def make_test_cache():
    """Makes a new cache client for testing."""
    return TestCache({
        1: ('inc', 'key__ver'),
        3: ('set', 'key', (2, ['interrupt']))
    })


@tests.test
def transaction_loop():
    """Transaction using for statement."""
    test_cache = make_test_cache()
    t = Transaction(test_cache, 'key')
    for ref in t:
        lst = ref() or []
        lst.append(1)
        ref(lst)
    assert ['interrupt', 1] == test_cache.get('key')[1]


@tests.test
def transaction_block():
    """Transaction using IoC."""
    def block(lst):
        if lst:
            lst.append(1)
            return lst
        return []
    test_cache = make_test_cache()
    t = Transaction(test_cache, 'key')
    t(block)
    assert ['interrupt', 1] == test_cache.get('key')[1]

