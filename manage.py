#!/usr/bin/env python

import os

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager
from flask_security.utils import encrypt_password

from app.extensions import user_datastore
from app.factory import create_app


manager = Manager(create_app)
manager.add_command('assets', ManageAssets())
manager.add_command('db', MigrateCommand)


@manager.command
def add_users():
    admin = user_datastore.find_or_create_role('admin')
    with open('users.txt') as f:
        users = (line.split(',') for line in f.readlines())
        for email, password, can_make_admin, can_accept in users:
            user = user_datastore.find_user(email=email.strip())
            if not user:
                user = user_datastore.create_user(
                    email=email.strip(),
                    roles=[admin],
                    is_superadmin=can_make_admin.strip() == '1',
                    can_accept_suits=can_accept.strip() == '1')
            user.active = True
            user.password = encrypt_password(password.strip())
            user_datastore.put(user)
    user_datastore.commit()


def set_env_vars(env_file, cmd='export', delim='=', quote=True):
    with open(env_file) as f:
        for line in f.readlines():

            if not line.strip() or line.startswith('#'):
                continue

            key, val = line.split('=', 1)

            if not key or not val:
                continue

            key = key.strip()
            val = val.strip()
            if quote:
                val = '"{}"'.format(val)
            print('{} {}{}{}'.format(cmd, key, delim, val))


@manager.command
def set_env():
    for env_file in os.scandir():
        if env_file.name.endswith('.env'):
            set_env_vars(env_file.name)


@manager.command
def set_cf_env():
    for env_file in os.scandir():
        if env_file.name.endswith('.env'):
            set_env_vars(
                env_file.name,
                cmd='cf set-env sue-my-brother',
                delim=' ',
                quote=False)


@manager.command
def runserver_ssl():
    manager.app.run(
        host='localhost',
        port=5443,
        ssl_context=('server.crt', 'server.key'))


if __name__ == '__main__':
    manager.run()
