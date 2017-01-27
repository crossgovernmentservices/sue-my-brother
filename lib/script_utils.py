import contextlib
import os
import pkg_resources
import subprocess
import sys
import venv

from lib.term_colour import notify, status_ok, status_err


@contextlib.contextmanager
def activate_virtualenv(env_dir):
    abs_env_dir = os.path.abspath(env_dir)

    os.environ['VIRTUAL_ENV'] = abs_env_dir
    os.environ['PATH'] = '{VIRTUAL_ENV}{sep}bin{pathsep}{PATH}'.format(
        sep=os.sep, pathsep=os.pathsep, **os.environ)

    if not os.path.isdir(abs_env_dir):
        create_virtualenv(abs_env_dir)

    if sys.platform == 'win32':
        site_packages = os.path.join(abs_env_dir, 'Lib', 'site-packages')
    else:
        site_packages = os.path.join(abs_env_dir, 'lib', 'python{}'.format(
            sys.version[:3]), 'site-packages')

    old_sys_path = list(sys.path)

    import site
    site.addsitedir(site_packages)

    sys.real_prefix = sys.prefix
    sys.prefix = abs_env_dir

    new_sys_path = []
    for item in list(sys.path):
        if item not in old_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path

    check_requirements(env_dir)

    yield


def create_virtualenv(env_dir):
    notify('\nCreating virtualenv')
    res = venv.create(env_dir, system_site_packages=False, with_pip=True)
    if not res:
        proc = subprocess.run(
            ['pip', 'install', '--upgrade', 'pip'],
            env=os.environ.copy())
        if proc.returncode:
            sys.exit(proc.returncode)
        status_ok('Done')
    return res


def install_requirements(env_dir):
    notify('\nInstalling requirements')
    env = os.environ.copy()
    proc = subprocess.run(
        ['pip', 'install', '-r', 'requirements.txt'],
        env=env)
    if proc.returncode:
        sys.exit(proc.returncode)
    status_ok('Done')


def check_requirements(env_dir):
    notify('\nChecking requirements')

    with open('requirements.txt', 'r') as req_file:
        dependencies = req_file.readlines()

    workingset = pkg_resources.WorkingSet(sys.path)

    fail = False
    for dep in dependencies:
        try:
            workingset.require(dep)

        except Exception as e:
            status_err(str(e))

            proc = subprocess.run(
                ['pip', 'install', dep],
                env=os.environ.copy())

            if proc.returncode:
                sys.exit(proc.returncode)

    if not fail:
        status_ok('OK')

    return not fail


def run_in_virtualenv(argv, env_dir='venv'):
    with activate_virtualenv(env_dir):
        env = os.environ.copy()
        proc = subprocess.run(argv, env=env)
        sys.exit(proc.returncode)


@contextlib.contextmanager
def virtualenv(env_dir='venv'):

    if os.environ.get('VIRTUAL_ENV') is None:
        run_in_virtualenv(sys.argv)

    else:
        yield


@contextlib.contextmanager
def environment(env_file='environment.sh'):
    if os.path.exists(env_file):
        os.environ.update(dict(env_vars_from_file(env_file)))
    yield


def env_vars_from_file(env_file):
    with open(env_file) as f:
        for line in f.readlines():
            if '=' in line:
                key, val = parse_env_var(line)
                if key and val:
                    yield key, val


def parse_env_var(line):
    key, val = line.split('=', 1)
    key = key.strip()
    if key.startswith('export '):
        key = key[7:]
    val = val.strip()
    return key, val
