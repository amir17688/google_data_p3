#!/usr/bin/env python
# encoding: utf-8
# vim: set et sw=4 ts=4 sts=4 fenc=utf-8
# Author: YuanLin


import tornado.web
import motor
from tornado import template
import redis

from . import settings as config
from .views import urls


class Application(tornado.web.Application):
    """App for project.
    """

    def __init__(self):
        settings = dict(
            static_path=config.STATIC,
            xsrf_cookies=False,
            cookie_secret=config.COOKIE_STR,
            login_url="/u/login",
            autoscape=None,
        )
        self.rdc = redis.StrictRedis(host="127.0.0.1", port=6379, db=0)
        self.db = motor.MotorClient(config.MONGO_URI).qfbot
        self.template = template.Loader(config.TEMPLATE)

        super(Application, self).__init__(urls, **settings)