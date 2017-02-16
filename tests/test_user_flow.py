# -*- coding: utf-8 -*-
"""
Test user flow
"""

import pytest
from bs4 import BeautifulSoup
from flask import url_for
from mock import Mock


mock_openid_config = Mock()
mock_openid_config.return_value = {
    'authorization_endpoint': 'http://dex.example.com:5556/auth',
    'discovery_url': 'http://dex.example.com:5556',
    'client_id': 'testid'}


def request(url, method, data=None):
    r = method(url, data=data)
    r.soup = BeautifulSoup(r.get_data(as_text=True), 'html.parser')
    return r


@pytest.fixture
def index(client):
    return request(url_for('main.index'), client.get)


@pytest.fixture
def details_form(client):
    return request(url_for('main.details'), client.get)


@pytest.fixture
def admin_users(client):
    return request(url_for('main.admin_users'), client.get)


@pytest.fixture
def post(client):

    def submit(url):

        def response(data):
            return request(url, client.post, data=data)

        return response

    return submit


@pytest.fixture
def post_details(post):
    return post(url_for('main.details'))


@pytest.fixture
def post_suit(post):
    return post(url_for('main.start_suit'))


@pytest.mark.usefixtures('db_session')
class WhenGettingStarted(object):

    def it_shows_a_call_to_action(self, index):
        links = index.soup.find_all('a', href=url_for('main.details'))
        assert 'Sue him now' in links[0].text

    def it_requests_user_details_if_unrecognized(self, details_form):
        heading = details_form.soup.find('h1')
        assert heading.text == 'Enter your own details'


class WhenEnteringPlaintiffDetails(object):

    def it_redirects_if_authn_user_has_name(self, logged_in, details_form):
        assert details_form.status_code == 302

    def it_prepopulates_authn_users_email(
            self, unnamed_user_logged_in, details_form):
        print(details_form.soup)
        email = details_form.soup.find('input', id='email')
        assert email['value'] == unnamed_user_logged_in.email

    def it_requires_a_full_name(self, post_details):
        errors = post_details({}).soup.find_all(class_='error')
        assert errors[0].parent.parent.find('label').text == 'Your Full Name'

    def it_requires_an_email_address(self, post_details):
        data = {'name': 'Test User'}
        errors = post_details(data).soup.find_all(class_='error')
        assert errors[0].parent.parent.find('label').text == \
            'Your Email Address'


class WhenEnteringSuitDetails(object):

    def it_requires_defendant_name(self, post_suit):
        errors = post_suit({}).soup.find_all(class_='error')
        assert errors[0].parent.parent.find('label').text == \
            'Your Brother\'s Full Name'
