# -*- coding: utf-8 -*-
"""
Flask assets bundles and filters
"""

import os

from flask_assets import Bundle, Environment

from lib.sass_filter import LibSass


def static(*path):
    return os.path.join(os.path.dirname(__file__), 'static', *path)


libsass_output = LibSass(include_paths=[
    static('sass'),
    static('govuk_frontend_toolkit/stylesheets'),
    static('govuk_elements/public/sass/elements')])

env = Environment()

env.register('css_govuk_elements', Bundle(
    'sass/govuk_elements.scss',
    filters=(libsass_output,),
    output='stylesheets/govuk_elements.css',
    depends=[
        '/static/govuk_elements/public/sass/**/*.scss',
        '/static/govuk_frontend_toolkit/stylesheets/**/*.scss']))

env.register('css_main', Bundle(
    'sass/main.scss',
    filters=(libsass_output,),
    output='stylesheets/main.css',
    depends=[
        '/static/sass/main/**/*.scss',
        '/static/govuk_frontend_toolkit/stylesheets/**/*.scss']))
