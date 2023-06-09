#!/usr/bin/env python2
# Copyright 2016 iNuron NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Watcher module for framework and volumedriver
"""

import sys
import time
import uuid
import logging
from ovs.extensions.storage.persistentfactory import PersistentFactory
from ovs.log.logHandler import LogHandler

logger = LogHandler.get('extensions', name='watcher')


def _log(log_target, entry, level):
    """
    Logs an entry
    """
    if level > 0:  # 0 = debug, 1 = info, 2 = error
        logger.debug('[{0}] {1}'.format(log_target, entry))


def services_running(target):
    """
    Check all services are running
    :param target: Target to check
    :return: Boolean
    """
    try:
        key = 'ovs-watcher-{0}'.format(str(uuid.uuid4()))
        value = str(time.time())

        if target == 'framework':
            # Volatile
            _log(target, 'Testing volatile store...', 0)
            max_tries = 5
            tries = 0
            while tries < max_tries:
                try:
                    try:
                        logging.disable(logging.WARNING)
                        from ovs.extensions.storage.volatilefactory import VolatileFactory
                        VolatileFactory.store = None
                        volatile = VolatileFactory.get_client()
                        volatile.set(key, value)
                        if volatile.get(key) == value:
                            volatile.delete(key)
                            break
                        volatile.delete(key)
                    finally:
                        logging.disable(logging.NOTSET)
                except Exception as message:
                    _log(target, '  Error during volatile store test: {0}'.format(message), 2)
                key = 'ovs-watcher-{0}'.format(str(uuid.uuid4()))  # Get another key
                time.sleep(1)
                tries += 1
            if tries == max_tries:
                _log(target, '  Volatile store not working correctly', 2)
                return False
            _log(target, '  Volatile store OK after {0} tries'.format(tries), 0)

            # Persistent
            _log(target, 'Testing persistent store...', 0)
            max_tries = 5
            tries = 0
            while tries < max_tries:
                try:
                    try:
                        logging.disable(logging.WARNING)
                        persistent = PersistentFactory.get_client()
                        persistent.set(key, value)
                        if persistent.get(key) == value:
                            persistent.delete(key)
                            break
                        persistent.delete(key)
                    finally:
                        logging.disable(logging.NOTSET)
                except Exception as message:
                    _log(target, '  Error during persistent store test: {0}'.format(message), 2)
                key = 'ovs-watcher-{0}'.format(str(uuid.uuid4()))  # Get another key
                time.sleep(1)
                tries += 1
            if tries == max_tries:
                _log(target, '  Persistent store not working correctly', 2)
                return False
            _log(target, '  Persistent store OK after {0} tries'.format(tries), 0)

        if target == 'volumedriver':
            # Arakoon, voldrv cluster
            _log(target, 'Testing arakoon (voldrv)...', 0)
            max_tries = 5
            tries = 0
            while tries < max_tries:
                try:
                    from ovs.extensions.db.etcd.configuration import EtcdConfiguration
                    from ovs.extensions.storage.persistent.pyrakoonstore import PyrakoonStore
                    cluster_name = str(EtcdConfiguration.get('/ovs/framework/arakoon_clusters|voldrv'))
                    client = PyrakoonStore(cluster=cluster_name)
                    client.set(key, value)
                    if client.get(key) == value:
                        client.delete(key)
                        break
                    client.delete(key)
                except Exception as message:
                    _log(target, '  Error during arakoon (voldrv) test: {0}'.format(message), 2)
                key = 'ovs-watcher-{0}'.format(str(uuid.uuid4()))  # Get another key
                time.sleep(1)
                tries += 1
            if tries == max_tries:
                _log(target, '  Arakoon (voldrv) not working correctly', 2)
                return False
            _log(target, '  Arakoon (voldrv) OK', 0)

        if target in ['framework', 'volumedriver']:
            # RabbitMQ
            _log(target, 'Test rabbitMQ...', 0)
            import pika
            from ovs.extensions.db.etcd.configuration import EtcdConfiguration
            rmq_servers = EtcdConfiguration.get('/ovs/framework/messagequeue|endpoints')
            good_node = False
            for server in rmq_servers:
                try:
                    connection_string = '{0}://{1}:{2}@{3}/%2F'.format(EtcdConfiguration.get('/ovs/framework/messagequeue|protocol'),
                                                                       EtcdConfiguration.get('/ovs/framework/messagequeue|user'),
                                                                       EtcdConfiguration.get('/ovs/framework/messagequeue|password'),
                                                                       server)
                    connection = pika.BlockingConnection(pika.URLParameters(connection_string))
                    channel = connection.channel()
                    channel.basic_publish('', 'ovs-watcher', str(time.time()),
                                          pika.BasicProperties(content_type='text/plain', delivery_mode=1))
                    connection.close()
                    good_node = True
                except Exception as message:
                    _log(target, '  Error during rabbitMQ test on node {0}: {1}'.format(server, message), 2)
            if good_node is False:
                _log(target, '  No working rabbitMQ node could be found', 2)
                return False
            _log(target, '  RabbitMQ test OK', 0)
            _log(target, 'All tests OK', 0)
            return True
    except Exception as ex:
        _log(target, 'Unexpected exception: {0}'.format(ex), 2)
        return False

if __name__ == '__main__':
    given_target = sys.argv[1]
    mode = sys.argv[2]
    _log(given_target, 'Starting service', 1)
    if mode == 'wait':
        _log(given_target, 'Waiting for master services', 1)
        while True:
            if services_running(given_target):
                _log(given_target, 'Master services available', 1)
                sys.exit(0)
            time.sleep(5)
    if mode == 'check':
        _log(given_target, 'Checking master services', 1)
        while True:
            if not services_running(given_target):
                _log(given_target, 'One of the master services is unavailable', 1)
                sys.exit(1)
            time.sleep(5)
    _log(given_target, 'Invalid parameter', 1)
    time.sleep(60)
    sys.exit(1)
