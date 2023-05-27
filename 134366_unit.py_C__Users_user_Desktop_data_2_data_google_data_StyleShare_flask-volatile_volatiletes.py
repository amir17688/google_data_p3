import os
import time
from attest import assert_hook, Tests
from werkzeug.contrib.cache import SimpleCache, MemcachedCache
from flask_volatile.unit import CacheUnit


tests = Tests()


def make_unit(store=None):
    """Creates a new empty cache unit."""
    store = store or SimpleCache()
    unit = CacheUnit(store, 'prefix')
    return unit, store


@tests.test
def subkey():
    """Creating subkeys."""
    unit, _ = make_unit()
    assert len(unit.subkey('abc')) > 3
    assert unit.subkey('abc').endswith('abc')
    assert not unit.subkey('abc').startswith('abc')


@tests.test
def set():
    """Tests set() method."""
    unit, store = make_unit()
    unit.set('abc', 123)
    unit.set('def', 456)
    assert unit.get('abc') == 123
    assert unit.get('def') == 456
    assert unit.get_many('abc', 'def') == [123, 456]
    assert store.get(unit.subkey('abc')) == 123
    assert store.get(unit.subkey('def')) == 456
    for ref in unit.subkeys_transaction:
        assert ref() == frozenset(['abc', 'def'])


@tests.test
def add():
    """Tests add() method."""
    unit, store = make_unit()
    unit.add('abc', 123)
    unit.add('def', 456)
    unit.add('def', 567)
    assert unit.get('abc') == 123
    assert unit.get('def') == 456
    assert unit.get_many('abc', 'def') == [123, 456]
    assert store.get(unit.subkey('abc')) == 123
    assert store.get(unit.subkey('def')) == 456
    for ref in unit.subkeys_transaction:
        assert ref() == frozenset(['abc', 'def'])


@tests.test
def set_delete_many():
    """Tests set_many() and delete_many() methods."""
    # set_many
    unit, store = make_unit()
    unit.set_many({'abc': 123, 'def': 456, 'ghi': 789, 'jkl': 123})
    assert unit.get('abc') == 123
    assert unit.get('def') == 456
    assert unit.get('ghi') == 789
    assert unit.get('jkl') == 123
    assert unit.get_many('abc', 'def', 'ghi', 'jkl') == [123, 456, 789, 123]
    assert store.get(unit.subkey('abc')) == 123
    assert store.get(unit.subkey('def')) == 456
    assert store.get(unit.subkey('ghi')) == 789
    assert store.get(unit.subkey('jkl')) == 123
    for ref in unit.subkeys_transaction:
        assert ref() == frozenset(['abc', 'def', 'ghi', 'jkl'])
    # delete_many
    unit.delete_many('def', 'jkl')
    assert unit.get('abc') == 123
    assert unit.get('def') is None
    assert unit.get('ghi') == 789
    assert unit.get('jkl') is None
    assert unit.get_many('abc', 'def', 'ghi', 'jkl') == [123, None, 789, None]
    assert store.get(unit.subkey('abc')) == 123
    assert store.get(unit.subkey('def')) is None
    assert store.get(unit.subkey('ghi')) == 789
    assert store.get(unit.subkey('jkl')) is None
    for ref in unit.subkeys_transaction:
        assert ref() == frozenset(['abc', 'ghi'])


@tests.test
def clear():
    """Tests clear() method."""
    unit, _ = make_unit()
    for i, a in enumerate('abcd'):
        for j, b in enumerate('abcd'):
            unit.set(a + b, i * 10 + j)
    for ref in unit.subkeys_transaction:
        assert len(ref()) == 16
    unit.clear()
    for ref in unit.subkeys_transaction:
        assert ref() == frozenset()


@tests.test
def inc_dec():
    """Tests inc() and dec() methods."""
    try:
        mc = os.environ['VOLATILETESTS_MEMCACHED']
    except KeyError:
        print 'VOLATILETESTS_MEMCACHED is not set; skipped'
        return
    mc = MemcachedCache([mc], key_prefix='volatiletests_%s' % time.time())
    def tpl(method, r1, r2):
        unit, store = make_unit(mc)
        op = getattr(unit, method)
        key = method + 'num'
        assert unit.get(key) is None
        assert store.get(unit.subkey(key)) is None
        for ref in unit.subkeys_transaction:
            assert ref() is None or key not in ref()
        unit.set(key, 5)
        op(key)
        assert unit.get(key) == r1
        assert store.get(unit.subkey(key)) == r1
        for ref in unit.subkeys_transaction:
            assert key in ref()
        op(key, 2)
        assert unit.get(key) == r2
        assert store.get(unit.subkey(key)) == r2
        for ref in unit.subkeys_transaction:
            assert key in ref()
    tpl('inc', 6, 8)
    tpl('dec', 4, 2)

