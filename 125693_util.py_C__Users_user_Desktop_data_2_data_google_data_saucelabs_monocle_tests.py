import time
from monocle import _o, util
from o_test import test


@test
@_o
def test_simple():
    t = time.time()
    yield util.sleep(0.01)
    dt = time.time() - t
    assert 0.005 < dt < 0.015
