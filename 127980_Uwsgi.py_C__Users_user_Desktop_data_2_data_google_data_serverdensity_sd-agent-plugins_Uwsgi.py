#!/usr/bin/env
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, \
    unicode_literals

import errno
import glob
import json
import socket

from contextlib import contextmanager
from collections import defaultdict


BUFFER_SIZE = 4096


@contextmanager
def connect_sock(address, socket_type=socket.AF_UNIX, timeout=1):
    sock = socket.socket(socket_type, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(address)
    try:
        yield sock
    finally:
        sock.close()


def read_sock(sock):
    buffers = []
    while True:
        try:
            buffer = sock.recv(BUFFER_SIZE)
        except IOError as err:
            if err.errno != errno.EINTR:
                raise
            continue
        else:
            if not buffer:
                break
            buffers.append(buffer)
    return b''.join(buffers)


class Uwsgi(object):
    '''
    Monitor uWSGI using the uWSGI stats server.

    Config should be in /etc/sd-agent/config.cfg like:

    [Uwsgi]
    socket_paths: /var/run/*_stats.sock

    Multiple paths to be monitored should be separated with a ','.
    Path supports globbing.
    '''

    def __init__(self, agent_config, logger, raw_config):
        self.agent_config = agent_config
        self.logger = logger
        self.raw_config = raw_config
        self.socket_paths = []
        self._parse_config()

    def run(self):
        stats = self._get_stats()
        return self._merge_stats(stats)

    def _parse_config(self):
        paths = self.raw_config['Uwsgi'].get('socket_paths')
        for path in paths.split(','):
            self.socket_paths += glob.glob(path)

    def _get_stats(self):
        result = []
        for socket_path in self.socket_paths:
            try:
                with connect_sock(socket_path) as sock:
                    data = read_sock(sock)
                    data = data.decode('utf8')
                    result.append(json.loads(data))
            except Exception:
                self.logger.exception('Cannot read socket %s', socket_path)
                continue
        return result

    def _merge_stats(self, stats):
        result = defaultdict(int)
        status_count = defaultdict(int)

        average_time = 0
        count = 0
        for process in stats:
            workers = process['workers']
            count += len(workers)

            for worker in workers:
                average_time += worker['avg_rt']
                status_count[worker['status']] += 1
                result['exception_count'] += worker['exceptions']
                result['harakiri_count'] += worker['harakiri_count']
                result['memory_rss'] += worker['rss']
                result['network_tx'] += worker['tx']
                result['request_count'] += worker['requests']
                result['respawn_count'] += worker['respawn_count']

        result['workers_count'] = count
        for status, count in status_count.items():
            key = 'workers_{0}_count'.format(status)
            result[key] = count

        result['request_avg_time'] = average_time / count if count else 0

        return dict(result)


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    fake_config = {'Uwsgi': {'socket_paths': '/tmp/*_stats.sock'}}
    uwsgi = Uwsgi({}, logging, fake_config)
    print(uwsgi.run())
