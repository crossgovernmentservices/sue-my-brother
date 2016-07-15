#!/usr/bin/env python

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager
from flask_security.utils import encrypt_password
import pytest

from app.extensions import user_datastore
from app.factory import create_app
from lib.govuk_assets import ManageGovUkAssets


manager = Manager(create_app)
manager.add_command('assets', ManageAssets())
manager.add_command('db', MigrateCommand)
manager.add_command('install_all_govuk_assets', ManageGovUkAssets())


suites = {
    'all': ['--start-live-server'],
    'coverage': ['--pyargs', 'tests.spec', '--cov=app', '--cov-report=html']
}


@manager.option(
    'suite', default='all', nargs='?', choices=suites.keys(),
    help='Specify test suite to run (default all)')
@manager.option('--spec', action='store_true', help='Output in spec style')
def test(spec, suite):
    """Runs tests"""
    args = []

    if spec:
        args.extend(['--spec'])

    if not suite:
        suite = 'all'

    args.extend(suites[suite])

    return pytest.main(args)


@manager.command
def add_users():
    admin = user_datastore.find_or_create_role('admin')
    with open('users.txt') as f:
        users = (line.split(',') for line in f.readlines())
        for email, password in users:
            user = user_datastore.find_user(email=email.strip())
            if not user:
                user = user_datastore.create_user(
                    email=email.strip(),
                    roles=[admin])
            user.active = True
            user.password = encrypt_password(password.strip())
            user_datastore.put(user)
    user_datastore.commit()


if __name__ == '__main__':
    manager.run()
