from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import numpy as np
import tensorflow as tf

from data import create_example
from ham import HAMOperations, HAMTree

tf.app.flags.DEFINE_float('lr', 0.001, 'Learning rate for Adam optimizer')
tf.app.flags.DEFINE_integer('batches_per_epoch', 1000, 'Number of batches per epoch')
tf.app.flags.DEFINE_integer('max_epochs', 100, 'Maximum epochs to train for')
tf.app.flags.DEFINE_integer('batch_size', 50, 'Batch size')
tf.app.flags.DEFINE_integer('n', 4, 'Size of the input to sort')
tf.app.flags.DEFINE_integer('embed_size', 10, 'Embedding size for input to sort - half key, half value')
tf.app.flags.DEFINE_integer('tree_size', 20, 'Tree size')
tf.app.flags.DEFINE_integer('controller_size', 20, 'Controller size')
tf.app.flags.DEFINE_string('weights_path', './ham.weights', 'Where to load and save the weights for the model')
tf.app.flags.DEFINE_boolean('test', False, 'Whether to only run testing')

config = tf.app.flags.FLAGS

inputs = tf.placeholder(tf.float32, shape=[config.batch_size, config.n, config.embed_size], name='Input')
control = tf.placeholder(tf.float32, shape=[config.batch_size, config.controller_size], name='Control')
target = tf.placeholder(tf.float32, shape=[config.batch_size, config.n, config.embed_size], name='Target')

ham_ops = HAMOperations(config.embed_size, config.tree_size, config.controller_size)
tree = HAMTree(ham_ops=ham_ops)
tree.construct(config.n)

values = [tf.squeeze(x, [1]) for x in tf.split(1, config.n, inputs)]
for i, val in enumerate(values):
  tree.leaves[i].embed(val)
tree.refresh()

calculate_predicted = tf.concat(1, [tree.get_output(control) for _ in xrange(config.n)])
targets = tf.reshape(target, [config.batch_size, config.n * config.embed_size])
penalty = lambda x, y: tf.pow(x - y, 2)
#penalty = lambda x, y: tf.abs(x - y)
calculate_loss = tf.reduce_sum(penalty(calculate_predicted, targets)) / config.n / config.batch_size

optimizer = tf.train.AdamOptimizer(config.lr)
train_step = optimizer.minimize(calculate_loss)

init = tf.initialize_all_variables()
saver = tf.train.Saver()

with tf.Session() as session:
  for var in tf.trainable_variables():
    tf.histogram_summary(var.op.name, var)
  summary_op = tf.merge_all_summaries()
  summary_writer = tf.train.SummaryWriter('/tmp/ham-sort/', session.graph_def, flush_secs=5)

  session.run(init)

  if os.path.exists(config.weights_path):
    saver.restore(session, config.weights_path)

  # Paper uses 100 epochs with 1000 batches of batch size 50
  for epoch in xrange(config.max_epochs):
    total_batches = config.batches_per_epoch
    total_accuracy = 0.0
    total_loss = 0.0
    for i in xrange(total_batches):
      X, Y = [], []
      for b in xrange(config.batch_size):
        x, y = create_example(n=config.n, bit_length=config.embed_size / 2)
        X.append(x)
        Y.append(y)
      control_signal = np.zeros([config.batch_size, config.controller_size], dtype=np.float32)
      feed = {inputs: X, target: Y, control: control_signal}
      _, loss, predicted = session.run([tf.no_op() if config.test else train_step, calculate_loss, calculate_predicted], feed_dict=feed)
      ###
      for b in xrange(config.batch_size):
        y = Y[b].reshape(config.n * config.embed_size)
        y_pred = np.rint(predicted[b]).astype(int)
        total_accuracy += (y == y_pred).all()
      total_loss += loss
    train_acc = total_accuracy / (config.batch_size * total_batches)
    train_loss = total_loss / total_batches
    print('Epoch = {}'.format(epoch))
    print('Loss = {}'.format(train_loss))
    print('Accuracy = {}'.format(train_acc))
    print('=-=')
    ###
    summary = tf.Summary()
    summary.ParseFromString(session.run(summary_op))
    summary.value.add(tag='TrainAcc', simple_value=float(train_acc))
    summary.value.add(tag='TrainLoss', simple_value=float(train_loss))
    summary_writer.add_summary(summary, epoch)
    ###
    if not config.test:
      saver.save(session, config.weights_path)
