# -*- coding: utf-8 -*-
"""
    taz.app
    ~~~~~~~~~

    This module implements the central WSGI application object.
    This is the extended Flask class with customized features

    :copyright: (c) 2014 by Bruno Rocha.
    :license: MIT, see LICENSE for more details.
"""

from flask import Flask


class Taz(Flask):
    """Flask is the WSGI application class and central object
    here it is extended to be customized as needes and to create
    a commom interface named `Taz`.

    Accepts the same parameters as Flask.

    Usually you create a Taz instance in your main module.
    the utility "taz startpeoject" will create it for you.

        from taz import Taz
        app = Taz(__name__)
    """
