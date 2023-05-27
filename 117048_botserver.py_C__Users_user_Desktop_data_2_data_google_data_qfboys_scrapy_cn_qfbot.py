#!/usr/bin/env python
# encoding: utf-8
# vim: set et sw=4 ts=4 sts=4 fenc=utf-8
# Author: YuanLin

import sys
import logging
import tornado.log
from tornado.options import options, define
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer

from crawl.application import Application

define('port', default=9030, help='serve on specify port', type=int)

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    channel = logging.StreamHandler(sys.stdout)
    options.parse_command_line()
    channel.setFormatter(tornado.log.LogFormatter())
    logger.addHandler(channel)

    http_server = HTTPServer(Application())
    http_server.bind(options.port)
    http_server.start()

    IOLoop.instance().start()

