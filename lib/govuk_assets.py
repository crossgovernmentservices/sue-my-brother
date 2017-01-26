# -*- coding: utf-8 -*-
"""
Manager command for installing GOV.UK assets
"""

import contextlib
import glob
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve
import zipfile


def install_govuk_assets(app_dir, logger=None):
    for package in ('frontend_toolkit', 'elements', 'template'):
        install(package, app_dir, logger)


def install(package, app_dir, logger=None):
    meta = package_metadata[package]

    def log(msg):
        return logger(msg) if logger else None

    if is_installed(meta, app_dir):
        return None

    log('Installing {}'.format(package))

    remove_package(meta, app_dir)

    with download_and_unzip(meta['url']) as unzip_dir:
        meta['install'](unzip_dir, app_dir, meta['dirs'])

    log('Done')


def is_installed(package, app_dir):
    return all([
        os.path.isdir(path.format(app_dir))
        for path in package['dirs'].values()])


def remove_govuk_assets(app_dir):
    for package in ('frontend_toolkit', 'elements', 'template'):
        remove_package(package_metadata[package], app_dir)


def remove_package(package, app_dir):
    for path in package['dirs'].values():
        rmdir(path.format(app_dir))


def install_frontend_toolkit(unzip_dir, app_dir, dirs):
    for path in ('images', 'javascripts', 'stylesheets'):
        move_dir(
            '{}/govuk_frontend_toolkit-master/{}'.format(unzip_dir, path),
            to=dirs['dest_dir'].format(app_dir))


def install_elements(unzip_dir, app_dir, dirs):
    move_dir(
        '{}/govuk_elements-master/public'.format(unzip_dir),
        to=dirs['dest_dir'].format(app_dir))


def install_template(unzip_dir, app_dir, dirs):
    master_dir = '{}/govuk_template-master'.format(unzip_dir)

    with pushd(master_dir):
        compile_template()

    move_dir(
        '{}/pkg/jinja_govuk_template*/assets'.format(master_dir),
        to=dirs['dest_assets'].format(app_dir))

    move_dir(
        '{}/pkg/jinja_govuk_template*/views'.format(master_dir),
        to=dirs['dest_views'].format(app_dir))


def compile_template():
    os.remove('.ruby-version')
    subprocess.call(['bundle', 'install'])
    subprocess.call(['bundle', 'exec', 'rake', 'build:jinja'])


package_metadata = {
    'frontend_toolkit': {
        'url': (
            'https://github.com/alphagov/govuk_frontend_toolkit/archive/'
            'master.zip'
        ),
        'dirs': {
            'dest_dir': '{}/static/govuk_frontend_toolkit'
        },
        'install': install_frontend_toolkit
    },
    'elements': {
        'url': 'https://github.com/alphagov/govuk_elements/archive/master.zip',
        'dirs': {
            'dest_dir': '{}/static/govuk_elements'
        },
        'install': install_elements
    },
    'template': {
        'url': 'https://github.com/alphagov/govuk_template/archive/master.zip',
        'dirs': {
            'dest_views': '{}/templates/govuk_template',
            'dest_assets': '{}/static/govuk_template'
        },
        'install': install_template
    }
}


@contextlib.contextmanager
def download_and_unzip(url):
    with TemporaryDirectory() as download_dir:
        dest_zip = '{}/package.zip'.format(download_dir)
        unzip_dir = '{}/unzipped'.format(download_dir)

        urlretrieve(url, dest_zip)

        with zipfile.ZipFile(dest_zip) as zf:
            zf.extractall(unzip_dir)

        yield unzip_dir


@contextlib.contextmanager
def pushd(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_cwd)


def move_dir(src, to):
    for f in glob.glob(src):

        if not os.path.isdir(to):
            os.makedirs(to)

        shutil.move(f, to)


def rmdir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
