import mock
import pytest
import time

from datetime import datetime
from flask import url_for
from mock import Mock, patch

from app.main.models import User, Suit
from app.main.views import authenticated_within

max_age = 50

mock_time_more_than_max_age = Mock()
mock_time_more_than_max_age.return_value = (
    time.mktime(datetime(2011, 6, 21, 10, 10, 0).timetuple()))

mock_time_less_than_max_age = Mock()
mock_time_less_than_max_age.return_value = (
    time.mktime(datetime(2011, 6, 21, 10, 0, max_age - 5).timetuple()))

mock_session = Mock()
mock_session = {
    'iat': time.mktime(datetime(2011, 6, 21, 10, 0, 0).timetuple())}

mock_openid_config = Mock()
mock_openid_config.return_value = {
    'authorization_endpoint':
    'http://dex.example.com:5556/auth',
    'discovery_url':
    'http://dex.example.com:5556',
    'client_id': None}


@pytest.yield_fixture
def mock_views_current_app_config():
    with mock.patch("app.main.views.current_app") as current_app:
        current_app.config.get.return_value = max_age
        yield


@pytest.yield_fixture
def mock_notify():
    with mock.patch("app.main.views.notify") as notify:
        notify.send_email.return_value = ""
        yield


@pytest.fixture
def test_suit(db_session):
    suit = Suit(
        plaintiff=User(
            email='plaintiff@example.com', name='Plaintiff Test', active=True
        ),
        defendant=User(
            email='defendant@example.com', name='Defendant Test', active=True
        )
    )
    db_session.add(suit)
    db_session.commit()
    return suit


@pytest.fixture
def post_accept_suit(client, test_suit):
    return client.post(url_for('main.accept', suit=test_suit.id),
                       follow_redirects=False)


class WhenTimeSinceLastAuthenticatedIsMoreThanMaxAge(object):

    @patch.dict('app.main.views.session', mock_session)
    @patch('time.time', mock_time_more_than_max_age)
    def it_returns_false(self, client):

        assert authenticated_within(max_age) is False


class WhenTimeSinceLastAuthenticatedIsLessThanMaxAge(object):

    @patch.dict('app.main.views.session', mock_session)
    @patch('time.time', mock_time_less_than_max_age)
    def it_returns_true(self, client):

        assert authenticated_within(max_age) is True


class WhenAcceptingASuitWithinAuthenticatedTime(object):

    @patch('time.time', mock_time_less_than_max_age)
    def it_redirects_to_admin(self, test_admin_user, client, test_suit,
                              mock_notify, mock_views_current_app_config):

        with client.session_transaction() as session:
            session['user_id'] = test_admin_user.id
            session['_fresh'] = False
            session['iat'] = mock_session['iat']

        response = client.post(url_for('main.accept', suit=test_suit.id))

        assert response.status_code == 302
        assert "/admin" in response.headers["Location"]


@pytest.mark.xfail(reason='reauthentication not yet implemented')
class WhenAcceptingASuitOutsideAuthenticatedTime(object):

    @patch('time.time', mock_time_more_than_max_age)
    def it_redirects_to_identity_broker(
            self, test_admin_user, client, test_suit,
            mock_views_current_app_config):

        with client.session_transaction() as session:
            session['user_id'] = test_admin_user.id
            session['_fresh'] = False
            session['iat'] = mock_session['iat']

        response = client.post(url_for('main.accept', suit=test_suit.id))

        assert response.status_code == 302
        assert "prompt=login" in response.headers["Location"]
