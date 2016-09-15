# -*- coding: utf-8 -*-
"""
Utility functions for use with Travis CI
"""

import contextlib
import os


RUNNING_ON_TRAVIS_CI = bool(os.environ.get('TRAVIS_CI', False))


@contextlib.contextmanager
def travis_fold(id):
    if RUNNING_ON_TRAVIS_CI:
        print('travis_fold:start:{}'.format(id))
    yield
    if RUNNING_ON_TRAVIS_CI:
        print('travis_fold:end:{}'.format(id))
