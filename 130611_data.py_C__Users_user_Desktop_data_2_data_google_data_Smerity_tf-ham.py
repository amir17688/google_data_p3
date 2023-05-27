from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

def create_pair(bit_length=5):
  key = np.random.randint(2, size=bit_length)
  val = np.random.randint(2, size=bit_length)
  return list(key), list(val)

def create_pairs(bit_length=5, n=5):
  pairs = [create_pair(bit_length=bit_length) for x in xrange(n)]
  return pairs

def concat_pairs(pairs):
  return [x + y for x, y in pairs]

def create_example(n=5, bit_length=5):
  pairs = create_pairs(n=n, bit_length=bit_length)
  correct_order = sorted(pairs, key=lambda p: p[0])
  x, y = concat_pairs(pairs), concat_pairs(correct_order)
  x, y = np.array(x, dtype=np.float32), np.array(y, dtype=np.float32)
  return x, y

if __name__ == '__main__':
  print('First two bits are the key which is used for sorting')
  print('Last two bits are the value that is tied to the key')
  print('Sorting should be stable and not depend on the value')
  for i in xrange(5):
    print('=-=')
    x, y = create_example(bit_length=2)
    print(x)
    print('=>', y)
