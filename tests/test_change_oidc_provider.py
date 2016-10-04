import pytest

from flask import url_for


def request(url, method, data=None):
    return method(url, data=data)


@pytest.fixture
def post(client):

    def submit(url):

        def response(data):
            return request(url, client.post, data=data)

        return response

    return submit


@pytest.fixture
def post_set_idp(post):
    url = url_for('base.set_idp', caller='.admin')
    return post(url)


class WhenUserChangesOIDCProvider(object):

    def it_sets_idp(self, post_set_idp):
        data = {'idp': 'test'}
        response = post_set_idp(data)

        cookies = response.headers.getlist('Set-Cookie')
        assert any("idp=test;" in s for s in cookies)
