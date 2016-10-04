import datetime
import pytest
import mock
from lib.oidc_old import verify_id_token
from flask import session, url_for

from app.blueprints.base.models import User
from app.extensions import oidc

from mock import patch

test_token_response = {
    'id_token': (
        'eyJhbGciOiJSUzI1NiIsImtpZCI6IjRmYjE1NjVlYWRlNTFiOWMzYTUyYmU0ND'
        'I0YjNjYTkxYzM4ZjUzNjUiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI4cHJZb1p5bTB6a3Q2'
        'WnpUSWJYYUZCUXZ0cldpMkE4eG1kQzlXRXozaTE0PUBsb2NhbGhvc3QiLCJlbWFpbCI6I'
        'mtlbi50c2FuZ0BkaWdpdGFsLmNhYmluZXQtb2ZmaWNlLmdvdi51ayIsImVtYWlsX3Zlcm'
        'lmaWVkIjp0cnVlLCJleHAiOjE0NzM4OTYzNjYsImlhdCI6MTQ3Mzg1MzE2NiwiaXNzIjo'
        'iaHR0cDovL2RleC5leGFtcGxlLmNvbTo1NTU2IiwibmFtZSI6IiIsInN1YiI6IjZjN2E5'
        'ZjQ1LTdmNTctNGQ5MS1iZTBlLTI4NjY3M2EyOGM2ZiJ9.tAVC2OD70vuTiARWoSagm37x'
        'QcWZ3o8W9jLvW8mHG39MgOp6GHGhyJuTgvkciDqi10SqHMcaGH9jSZepVUkQBNYPKejp9'
        'VZ3iiXyq731ckzoY93q5TvSOqjkoG7_HxXCkD5RX2F6XdTq_Se231TSEgWPxYl3ycLzKt'
        'NMeD5o3Aq8z_ypzgl7kQmEEdZWPSAcQr7-6IIHJ38UgDZfPhTYtUB4f_abgXXcuQV10uW'
        'kXBMdOzfM2s9ByexSAvL2-HVs_jtdC3C-Rwu_05yKfduVO5yiNBxoyrkv2yZgEhfKNh1W'
        'LYj2cb08cs4iw4u8QSEOSEzL5Gy1wXPdL78aoaqUYg')}


@pytest.fixture
def claims(utcnow):
    config = {
        "client_id":
            "8prYoZym0zkt6ZzTIbXaFBQvtrWi2A8xmdC9WEz3i14=@localhost",
        "keys": [
            {
                "kid": "4fb1565eade51b9c3a52be4424b3ca91c38f5365",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "e": "AQAB",
                "n": (
                    "zzJAqac1b3GVEehBZUp48gjJpXkD-vGsFyeTmWJGl00NVmgimW-h7"
                    "UUrVtJiwnaXS98D3ZPFnQRUrn1bmLeADkHs2sbWyfCNTYVK2sBY0Y"
                    "K6AamIwCLEET8aWB2b0P6L7xpM8lP8y3ss42ICgWV73txv-KwI8Fw"
                    "aDScIzSzSSdWWgqxh54PCMGAbWJCg6kjyufBocBVaZLUL_4HKIixI"
                    "SgyThUpFYND8iaQThI6fkW5o3Qc95AEcm5XKvlEXYv-BWWj-xBXka"
                    "FDy9YOjUKAXcYmWPhbY5LGM1GYk79PigNggxgRDsrxWDNQUzH25o8"
                    "wxRfOX1cZ-bdVzGYHDYeUbpw=="
                )
            }
        ]
    }
    now = datetime.datetime(2016, 9, 14, 12, 40)
    with utcnow("jose.jwt.datetime", now):
        claims = verify_id_token(test_token_response['id_token'], config)

    return claims

expected_issue_timestamp = 1473853166


@pytest.yield_fixture
def mock_auth(claims):
    with mock.patch("app.blueprints.base.views.oidc") as oidc:
        oidc.authenticate.return_value = claims
        yield


class WhenClientReceivesAnIDToken(object):

    def it_contains_an_auth_time_claim(self, claims):
        assert claims["iat"] == expected_issue_timestamp


class WhenUserIsAuthenticated(object):

    def it_stores_issuer_and_subject_id(self, mock_auth, client, db_session):

        expected_claims = {
            'email': 'ken.tsang@digital.cabinet-office.gov.uk',
            'issuer_id': 'http://dex.example.com:5556',
            'subject_id': '6c7a9f45-7f57-4d91-be0e-286673a28c6f'
        }

        response = client.get(url_for("base.oidc_callback"))
        assert response.status_code == 302

        users = User.query.filter_by(**expected_claims).all()
        assert len(users) == 1

    def it_is_possible_to_get_iat(self, mock_auth, client, db_session):

        response = client.get(url_for("base.oidc_callback"))
        assert response.status_code == 302

        assert session['iat'] == expected_issue_timestamp


def mock_requests_get(*args, **kwargs):
    class MockResponse:

        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if 'https://login.microsoftonline.com/testid' in args[0]:
        return MockResponse({
            'authorization_endpoint':
                'https://login.microsoftonline.com/testid/oauth2/authorize',
            'discovery_url':
                'https://login.microsoftonline.com/testid'}, 200)
    else:
        return MockResponse({}, 404)


class WhenUserAuthenticatesWithAzureADProvider(object):

    @patch('lib.oidc_old.requests.get', mock_requests_get)
    def it_retrieves_correct_authorization_endpoint(self, app):
        app.config["OIDC_PROVIDERS"] = {
            'dex': {'discovery_url': 'http://dex.example.com:5556'},
            'azure_ad': {'discovery_url': 'https://login.microsoftonline.'
                         'com/testid'}
        }
        oidc.init_app(app)
        config = oidc.openid_config("azure_ad")
        assert config['authorization_endpoint'] == (
            'https://login.microsoftonline.com/testid/oauth2/authorize')
