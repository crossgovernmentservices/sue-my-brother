# -*- coding: utf-8 -*-
"""
Application configuration
"""

import os


# get settings from environment, or credstash if running in AWS
env = os.environ
if env.get('SETTINGS') == 'AWS':
    from lib.aws_env import env


APP_NAME = env.get('APP_NAME', 'smb')

PREFERRED_URL_SCHEME = 'https'

SERVER_NAME = env.get(
    'SERVER_NAME', 'localhost:{}'.format(env.get('PORT', 5000)))

DB = {
    'user': env.get('DB_USERNAME'),
    'pass': env.get('DB_PASSWORD'),
    'host': env.get('DB_HOST'),
    'port': env.get('DB_PORT'),
    'name': env.get('DB_NAME', APP_NAME)
}

DEBUG = bool(env.get('DEBUG', True))

GOVUK_NOTIFY = {
    'disabled': 'GOVUK_NOTIFY_BASE_URL' not in env,
    'base_url': env.get('GOVUK_NOTIFY_BASE_URL'),
    'service_url': env.get('GOVUK_NOTIFY_SERVICE_URL'),
    'client_id': env.get('GOVUK_NOTIFY_SERVICE_ID'),
    'secret': env.get('GOVUK_NOTIFY_API_KEY'),
    'templates': {
        'accept': env.get('GOVUK_NOTIFY_TEMPLATE_ID_ACCEPT'),
        'sms': env.get('GOVUK_NOTIFY_TEMPLATE_ID_SMS')
    }
}

GOVUK_PAY = {
    'disabled': 'GOVUK_PAY_BASE_URL' not in env,
    'base_url': env.get('GOVUK_PAY_BASE_URL'),
    'api_key': env.get('GOVUK_PAY_API_KEY')
}

OIDC_CLIENT = {
    'issuer': env.get('OIDC_CLIENT_ISSUER'),
    'client_id': env.get('OIDC_CLIENT_ID'),
    'client_secret': env.get('OIDC_CLIENT_SECRET'),
}

# XXX This should be True when served over HTTPS
OIDC_COOKIE_SECURE = False

OIDC_GOOGLE_APPS_DOMAIN = env.get('OIDC_GOOGLE_APPS_DOMAIN')

SECRET_KEY = env.get(
    'SECRET_KEY',
    b'p{\xa7\x18K\rB\x06\xc5\xbdK?\xe5\xdb\xde\x02P\xd0,\x14\xe50\x07\xdd')


SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(
    os.path.join(os.path.dirname(__file__), '../{}.db'.format(DB['name'])))

if all(DB.values()):
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://{user}:{pass}@{host}:{port}/{name}'.format(**DB))

# Cloud Foundry provides DATABASE_URL
if 'DATABASE_URL' in env:
    SQLALCHEMY_DATABASE_URI = env.get('DATABASE_URL')

ACCEPT_SUIT_MAX_AGE = 300

# XXX Don't change the following settings unless necessary

# Skips concatenation of bundles if True, which breaks everything
ASSETS_DEBUG = False

ASSETS_LOAD_PATH = [
    'app/static',
    'app/templates']

LOGGING = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(name)s [%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'DEBUG'
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'level': 'DEBUG',
            'filename': '/tmp/gateway.log',
        }
    },
    'loggers': {
        'app.factory': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'waitress': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file'],
    },
}

# Calculate friendly times using UTC instead of local timezone
HUMANIZE_USE_UTC = True

SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = SECRET_KEY

# TODO this should be True when served via HTTPS
SESSION_COOKIE_SECURE = False

# Track modifications of objects and emit signals. Requires extra memory.
SQLALCHEMY_TRACK_MODIFICATIONS = False
