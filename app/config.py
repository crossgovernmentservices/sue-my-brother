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

DB = {
    'user': env.get('DB_USERNAME'),
    'pass': env.get('DB_PASSWORD'),
    'host': env.get('DB_HOST'),
    'port': env.get('DB_PORT'),
    'name': env.get('DB_NAME', APP_NAME)
}

DEBUG = bool(env.get('DEBUG', True))

OIDC_PROVIDERS = {
    'dex': {
        'discovery_url': env.get('DEX_APP_DISCOVERY_URL'),
        'client_id': env.get('DEX_APP_CLIENT_ID'),
        'client_secret': env.get('DEX_APP_CLIENT_SECRET'),
        'redirect_uri': env.get('DEX_APP_REDIRECT_URI')
    }
}

SECRET_KEY = env.get('SECRET_KEY', b'\x07\x7f\x02p\xf4\xa0\xe8\xc0lA\x9e\xdbK\xdb\x1b\xd3\x81=\x1d\xec\\\xd7\xbe\x06')


SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/{}'.format(DB['name'])
if all(DB.values()):
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://{user}:{pass}@{host}:{port}/{name}'.format(**DB))

# Cloud Foundry provides DATABASE_URL
if 'DATABASE_URL' in env:
    SQLALCHEMY_DATABASE_URI = env.get('DATABASE_URL')


# XXX Don't change the following settings unless necessary

# Skips concatenation of bundles if True, which breaks everything
ASSETS_DEBUG = False

ASSETS_LOAD_PATH = [
    'app/static',
    'app/templates']

# Calculate friendly times using UTC instead of local timezone
HUMANIZE_USE_UTC = True

SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = SECRET_KEY

# TODO this should be True when served via HTTPS
SESSION_COOKIE_SECURE = False

# Track modifications of objects and emit signals. Requires extra memory.
SQLALCHEMY_TRACK_MODIFICATIONS = False
