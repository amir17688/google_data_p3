from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf


class Transformer(object):
  '''
  Input = [b]
  Output = [d]
  '''
  def __init__(self, input_size, output_size):
    self.W = tf.Variable(tf.truncated_normal([input_size, output_size]))

  def __call__(self, val):
    return tf.nn.relu(tf.matmul(val, self.W))


class Join(object):
  '''
  Input = [d, d]
  Output = [d]
  '''
  def __init__(self, d):
    self.W = tf.Variable(tf.truncated_normal([2 * d, d]))

  def __call__(self, left, right):
    return tf.nn.relu(tf.matmul(tf.concat(1, [left, right]), self.W))


class Search(object):
  '''
  Input = [d, l]
  Output = [1]
  '''
  def __init__(self, d, l):
    self.W = tf.Variable(tf.truncated_normal([d + l, 1]))

  def __call__(self, h, control):
    return tf.nn.sigmoid(tf.matmul(tf.concat(1, [h, control]), self.W))


class Write(object):
  '''
  Input = [d, l]
  Output = [d]
  '''
  def __init__(self, d, l):
    self.H = tf.Variable(tf.truncated_normal([d + l, d]))
    self.T = tf.Variable(tf.truncated_normal([d + l, 1]))

  def __call__(self, h, control):
    data = tf.concat(1, [h, control])
    candidate = tf.nn.sigmoid(tf.matmul(data, self.H))
    update = tf.nn.sigmoid(tf.matmul(data,  self.T))
    return update * candidate + (1 - update) * h


class HAMOperations(object):
  def __init__(self, embed_size, tree_size, controller_size):
    ###
    # From the paper,
    self.embed_size = embed_size  # b
    self.tree_size = tree_size  # d
    self.controller_size = controller_size  # l
    ##
    self.transform = Transformer(embed_size, tree_size)
    self.join = Join(tree_size)
    self.search = Search(tree_size, controller_size)
    self.write = Write(tree_size, controller_size)


class HAMTree(object):
  def __init__(self, ham_ops):
    self.ops = ham_ops
    ##
    self.transform = self.ops.transform
    self.join = self.ops.join
    self.search = self.ops.search
    self.write = self.ops.write
    ##
    self.root = None
    self.leaves = None
    self.nodes = None

  def __repr__(self):
    return 'HAMTree'

  def construct(self, total_leaves):
    # Ensure that the total number of leaves is a power of two
    depth = np.log(total_leaves) / np.log(2)
    assert depth.is_integer(), 'The total leaves must be a power of two'
    ###
    # Create all the leaf nodes and then combine them until only one exists
    # A B C D
    # C D [A B]
    # [A B] [C D]
    # [[A B] [C D]]
    ###
    queue = [HAMNode(tree=self, left=None, right=None) for leaf in xrange(total_leaves)]
    self.leaves = [leaf for leaf in queue]
    self.nodes = [leaf for leaf in queue]
    while len(queue) > 1:
      l, r = queue.pop(0), queue.pop(0)
      node = HAMNode(tree=self, left=l, right=r)
      queue.append(node)
      self.nodes.append(node)
    self.root = queue[0]

  def refresh(self):
    self.root.join()

  def get_output(self, control):
    return self.root.retrieve_and_update(control)


class HAMNode(object):
  def __init__(self, tree, left, right):
    self.tree = tree
    self.left = left
    self.right = right
    self.h = None
    self.value = None

  def __repr__(self):
    return 'HAMNode(tree={}, left={}, right={})'.format(self.tree, bool(self.left), bool(self.right))

  def embed(self, value):
    self.value = value
    self.h = self.tree.transform(value)

  def join(self):
    if self.left and self.right:
      self.left.join()
      self.right.join()
      self.h = self.tree.join(self.left.h, self.right.h)

  def retrieve_and_update(self, control, attention=1.0):
    value = None
    ###
    # Retrieve the value - left and right weighted by the value of search
    if self.left and self.right:
      move_right = self.tree.search(self.h, control)
      value = self.right.retrieve_and_update(control, attention=attention * move_right)
      value += self.left.retrieve_and_update(control, attention=attention * (1 - move_right))
    else:
      value = attention * self.value
    ###
    # Update the values of the tree
    if self.left and self.right:
      self.h = self.tree.join(self.left.h, self.right.h)
    else:
      self.h = attention * self.tree.write(self.h, control) + (1 - attention) * self.h
    return value

if __name__ == '__main__':
  ham_ops = HAMOperations(1, 2, 3)
  tree = HAMTree(ham_ops=ham_ops)
  tree.construct(2)
  print(tree.nodes)
  l, r = tree.leaves
  assert len(tree.leaves) == 2, 'Depth 2 tree should have 2 leaves'
  assert len(tree.nodes) == 3, 'Depth 2 tree should have 3 nodes (two leaves, one root)'
  assert tree.root.left == l and tree.root.right == r, 'Depth 2 tree is broken'