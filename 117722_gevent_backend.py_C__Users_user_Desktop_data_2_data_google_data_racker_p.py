# Copyright 2013 Rackspace
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__all__ = [
    'initialize',
    'get_pool',
    'run_function',
    'join_pool'
]

from gevent import monkey
from gevent.pool import Pool


def initialize():
    monkey.patch_socket()
    monkey.patch_ssl()


def get_pool(size=10):
    pool = Pool(size)
    return pool


def run_function(pool, func, *args, **kwargs):
    return pool.spawn(func, *args, **kwargs)


def join_pool(pool):
    pool.join()
    return pool
