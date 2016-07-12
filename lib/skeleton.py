# -*- coding: utf-8 -*-
"""
Skeleton Flask app
"""

import inspect
import os

from flask import Blueprint, Flask, render_template


def context_processor(fn):
    fn.__context_processor__ = True
    return fn


def register_error_handlers(app):
    """
    Assign error page templates to all error status codes we care about
    """

    error_handlers = {
        '404.html': [404],
        # avoid flask 0.11 bug with 402 and 407
        '4xx.html': [401, 405, 406, 408, 409],
        '5xx.html': [500, 501, 502, 503, 504, 505]}

    def make_handler(code, template):
        template = os.path.join('errors', template)

        def handler(e):
            return render_template(template, code=code), code

        return handler

    for template, codes in error_handlers.items():
        for code in codes:
            app.register_error_handler(code, make_handler(code, template))


class AppFactory(object):

    def __new__(cls, config='config.py', **kwargs):
        root_path = os.path.dirname(inspect.getfile(cls))
        app = Flask(__name__, root_path=root_path)
        config_filename = os.path.join(root_path, config)
        app.config.from_pyfile(config_filename)
        app.config.update(kwargs)

        cls.register_blueprints(app)
        cls.register_context_processors(app)
        register_error_handlers(app)
        cls.register_extensions(app)

        return app

    @classmethod
    def register_blueprints(cls, app):
        for attr, value in cls.__dict__.items():
            if isinstance(value, Blueprint):
                app.register_blueprint(value)

    @classmethod
    def register_context_processors(cls, app):
        for attr, value in cls.__dict__.items():
            if callable(value) and hasattr(value, '__context_processor__'):
                app.context_processor(value)

    @classmethod
    def register_extensions(cls, app):
        for attr, value in cls.__dict__.items():
            if hasattr(value, 'init_app') and callable(value.init_app):
                value.init_app(app)
