# Copyright 2014 Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A clone of the default copy.deepcopy that doesn't handle cyclic
structures or complex types except for dicts and lists. This is
because gyp copies so large structure that small copy overhead ends up
taking seconds in a project the size of Chromium."""
import sys


_PYTHON3 = sys.version_info >= (3, 0, 0)


if _PYTHON3:
  long = int
  unicode = str


class Error(Exception):
  pass

__all__ = ["Error", "deepcopy"]

def deepcopy(x):
  """Deep copy operation on gyp objects such as strings, ints, dicts
  and lists. More than twice as fast as copy.deepcopy but much less
  generic."""

  try:
    return _deepcopy_dispatch[type(x)](x)
  except KeyError:
    raise Error('Unsupported type %s for deepcopy. Use copy.deepcopy ' +
                'or expand simple_copy support.' % type(x))

_deepcopy_dispatch = d = {}

def _deepcopy_atomic(x):
  return x

for x in (type(None), int, long, float,
          bool, str, unicode, type):
  d[x] = _deepcopy_atomic

def _deepcopy_list(x):
  return [deepcopy(a) for a in x]
d[list] = _deepcopy_list

def _deepcopy_dict(x):
  y = {}
  for key, value in x.items():
    y[deepcopy(key)] = deepcopy(value)
  return y
d[dict] = _deepcopy_dict

del d


# vim: expandtab tabstop=2 shiftwidth=2:
