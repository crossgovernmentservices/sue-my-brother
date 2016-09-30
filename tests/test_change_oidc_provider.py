import pytest

from flask import url_for


def request(url, method, data=None):
    r = method(url, data=data)
    return r


@pytest.fixture
def post(client):

    def submit(url):

        def response(data):
            return request(url, client.post, data=data)

        return response

    return submit


@pytest.fixture
def post_switch_oidc_provider(post):
    return post(url_for('base.switch_oidc_provider', caller='.admin'))


class WhenUserChangesOIDCProvider(object):

    def it_stores_new_oidc_provider_in_cookie(self,
                                              post_switch_oidc_provider):
        data = {'oidc_provider': 'test'}
        response = post_switch_oidc_provider(data)

        cookies = response.headers.getlist('Set-Cookie')
        assert any("oidc_provider=test;" in s for s in cookies)
