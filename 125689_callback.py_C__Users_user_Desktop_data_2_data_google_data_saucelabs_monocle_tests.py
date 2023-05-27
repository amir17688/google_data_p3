import pytest
from monocle import _o
from monocle.callback import Callback, defer
from o_test import test


@test
@_o
def test_result():
    cb = Callback()
    assert not hasattr(cb, 'result')
    cb('ok')
    assert cb.result == 'ok'


@test
@_o
def test_add():
    cb = Callback()
    calls = []
    assert cb._handlers == []
    cb.add(calls.append)
    assert cb._handlers == [calls.append]
    pytest.raises(TypeError, cb.add, False)
    assert cb._handlers == [calls.append]
    assert calls == []
    cb('ok')
    assert calls == ['ok']
    cb.add(calls.append)
    assert calls == ['ok', 'ok']
    pytest.raises(TypeError, cb.add, False)


@test
@_o
def test_defer():
    cb = defer('ok')
    assert isinstance(cb, Callback)
    assert cb.result == 'ok'
    calls = []
    cb.add(calls.append)
    assert calls == ['ok']
