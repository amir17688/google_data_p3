# -*- coding: utf-8 -*-

import os
from flask import Flask
from .core import db, cache, auth
from .helpers import register_blueprints
from .middleware import HTTPMethodOverrideMiddleware
import gitmodels


def create_app(package_name, package_path, settings_override=None):
    """Returns a :class:`Flask` application instance configured with common
    functionality for the Overholt platform.

    :param package_name: application package name
    :param package_path: application package path
    :param settings_override: a dictionary of settings to override
    :param register_security_blueprint: flag to specify if the Flask-Security
                                        Blueprint should be registered. Defaults
                                        to `True`.
    """
    app = Flask(package_name, instance_relative_config=True, instance_path=os.path.dirname(__file__))

    #app.config.from_object('vilya.settings')
    app.config.from_pyfile("settings.py")
    app.config.from_pyfile("settings-dev.py", silent=True)
    app.config.from_object(settings_override)

    db.init_app(app)
    cache.init_app(app)
    gitmodels.init_app(app)
    auth.init_app(app, db)

    register_blueprints(app, package_name, package_path)

    app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)

    return app
