#!/usr/bin/env python

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager
import pytest

from app.factory import SueMyBrother
from lib.govuk_assets import ManageGovUkAssets


manager = Manager(SueMyBrother)
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


if __name__ == '__main__':
    manager.run()
