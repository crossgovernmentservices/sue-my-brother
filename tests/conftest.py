import contextlib
import datetime
import mock
import os
import subprocess

from flask_migrate import upgrade
import pytest
from responses import RequestsMock
import sqlalchemy

from app.main.models import User
from app.config import SQLALCHEMY_DATABASE_URI
from app.extensions import db as _db, user_datastore
from app.factory import create_app
from tests.oidc_testbed import MockOIDCProvider


TEST_DATABASE_URI = SQLALCHEMY_DATABASE_URI + '_test'

config = {
    'issuer': 'http://example.com',
}


@pytest.yield_fixture(scope='session')
def responses():
    with RequestsMock(assert_all_requests_are_fired=False) as patch:
        yield patch


@pytest.yield_fixture(scope='session')
def provider(responses):
    op = MockOIDCProvider(responses, config)
    op.init_endpoints()
    yield op
    op.remove_endpoints()


@pytest.yield_fixture(scope='session')
def app(provider):
    app = create_app(**{
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'PREFERRED_URL_SCHEME': 'http',
        'WTF_CSRF_ENABLED': False,
        'OIDC_CLIENT': {
            'issuer': config['issuer'],
            'client_id': 'test-client',
            'client_secret': 'test-secret'
        },
        'OIDC_PROVIDER': {
            'issuer': 'https://localhost:5000',
            'subject_id_hash_salt': 'salt'
        }
    })

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


def reset_migrations(db):

    # reset migrations, otherwise they will not be reapplied
    conn = db.engine.connect()

    try:
        conn.execute('DELETE FROM alembic_version')

    except sqlalchemy.exc.ProgrammingError:
        pass

    finally:
        conn.close()


def teardown_db(db_url, db):

    if db_url.drivername == 'postgresql':
        db.drop_all()
        reset_migrations(db)

    if db_url.drivername == 'sqlite':
        if os.path.exists(db_url.database):
            os.unlink(db_url.database)


def init_db(db_url, db):
    sqlalchemy.orm.configure_mappers()

    try:
        teardown_db(db_url, db)

    except sqlalchemy.exc.OperationalError as e:
        if 'does not exist' in str(e):
            create_db(db_url)
            init_db(db_url, db)

    upgrade()


def create_db(db_url):
    dbname = db_url.database

    if db_url.drivername == 'postgresql':
        subprocess.call(['/usr/bin/env', 'createdb', dbname], timeout=1)

    if db_url.drivername == 'sqlite':
        # created automatically by migrations
        pass


@pytest.yield_fixture(scope='session')
def db(request, app):
    _db.app = app
    db_url = sqlalchemy.engine.url.make_url(TEST_DATABASE_URI)

    init_db(db_url, _db)

    yield _db

    teardown_db(db_url, _db)


@pytest.yield_fixture(scope='function')
def db_session(db, request):
    connection = db.engine.connect()
    transaction = connection.begin()

    session_factory = sqlalchemy.orm.sessionmaker(bind=connection)
    db.session = session = sqlalchemy.orm.scoped_session(session_factory)

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def selenium(db, live_server, selenium):
    """Override selenium fixture to always use flask live server"""
    return selenium


@pytest.fixture
def test_user(db_session):
    user = User(email='test@example.com', name='Test Test', active=True)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_admin_user(db_session):
    admin = user_datastore.find_or_create_role('admin')
    user = user_datastore.create_user(
        email="admin@example.com",
        roles=[admin],
        is_superadmin=True,
        can_accept_suits=True)
    user_datastore.commit()
    return user


@pytest.fixture
def unnamed_user(db_session):
    user = User(email='test@example.com', active=True)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.yield_fixture
def login(client):

    def do_login(user):
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

    yield do_login

    with client.session_transaction() as session:
        del session['user_id']
        del session['_fresh']


@pytest.yield_fixture
def unnamed_user_logged_in(unnamed_user, login):
    login(unnamed_user)
    yield unnamed_user


@pytest.yield_fixture
def logged_in(test_user, login):
    login(test_user)
    yield test_user


@pytest.yield_fixture
def admin_logged_in(test_admin_user, login):
    login(test_admin_user)
    yield test_admin_user


@pytest.fixture
def utcnow():
    @contextlib.contextmanager
    def patch_now(module, val):
        with mock.patch(module) as dt:
            dt.utcnow.return_value = val
            dt.side_effect = datetime.datetime
            yield
    return patch_now
