from functools import wraps
import json
from urllib.parse import urlencode, urlparse, urlunparse

from flask import current_app, g, request, session
from flask_oidc import MemoryCredentials, OpenIDConnect, logger
from itsdangerous import (
    JSONWebSignatureSerializer,
    TimedJSONWebSignatureSerializer)
from flask_security import current_user, login_user, logout_user
import httplib2
from oauth2client.client import (
    OAuth2Credentials,
    OAuth2WebServerFlow)
import requests


EXEMPT_METHODS = set(['OPTIONS'])


def sanitize_url(url):

    if url:
        parts = list(urlparse(url))
        parts[0] = ''
        parts[1] = ''
        parts[3] = ''
        url = urlunparse(parts[:6])

    return url


def oauth_flow(data, scope, redirect_uri=None, cache=None, login_hint=None,
               device_uri=None):

    if data['type'] in ('web', 'installed'):
        kwargs = {
            'redirect_uri': redirect_uri,
            'auth_uri': data['authorization_endpoint'],
            'token_uri': data['token_endpoint'],
            'login_hint': login_hint,
            'revoke_uri': data.get('revocation_endpoint'),
            'device_uri': data.get('device_uri'),
        }
        if kwargs['revoke_uri'] is None:
            del kwargs['revoke_uri']
        if kwargs['device_uri'] is None:
            del kwargs['device_uri']

        return OAuth2WebServerFlow(
            data['client_id'], data['client_secret'], scope, **kwargs)


class ExpiredIDToken(Exception):

    def __str__(self):
        return 'Expire ID token, credentials missing'


def cache(cache_obj, attr):

    def decorator(fn):

        @wraps(fn)
        def cached(*args, **kwargs):

            if attr in cache_obj:
                return getattr(cache_obj, attr)

            retval = fn(*args, **kwargs)
            setattr(cache_obj, attr, retval)
            return retval

        return cached

    return decorator


def check_csrf_token(csrf_token):
    if csrf_token != session.pop('oidc_csrf_token'):
        raise Exception('CSRF token mismatch')


class OIDCClient(OpenIDConnect):

    def __init__(self, app=None, credentials_store=None):
        self._config = {}
        self.credentials_store = credentials_store or MemoryCredentials()

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        self.set_default_config(app)

        self.add_callback_route(app)

        config = app.config['OIDC']
        self.disabled = config.get('disabled', False)

        if self.disabled:
            return

        self.add_request_decorators(app)

        config.update(self.openid_config(config.get('issuer', {})))
        self.flow = oauth_flow(config, app.config['OIDC_SCOPES'])
        assert isinstance(self.flow, OAuth2WebServerFlow)

        secret = app.config['SECRET_KEY']
        self.destination_serializer = JSONWebSignatureSerializer(secret)
        self.cookie_serializer = TimedJSONWebSignatureSerializer(secret)

        self.credentials_store = app.config.get(
            'OIDC_CREDENTIALS_STORE', self.credentials_store)

    def set_default_config(self, app):

        # default config options
        seven_days = 7 * 24 * 60 * 60
        app.config.setdefault('OIDC_SCOPES', ['openid', 'email'])
        app.config.setdefault('OIDC_GOOGLE_APPS_DOMAIN', None)
        app.config.setdefault('OIDC_ID_TOKEN_COOKIE_NAME', 'oidc_id_token')
        app.config.setdefault('OIDC_ID_TOKEN_COOKIE_TTL', seven_days)
        app.config.setdefault('OIDC_COOKIE_SECURE', app.debug)
        app.config.setdefault('OIDC_VALID_ISSUERS', [
            'https://accounts.google.com',
        ])
        app.config.setdefault('OIDC_CLOCK_SKEW', 60)
        app.config.setdefault('OIDC_REQUIRE_VERIFIED_EMAIL', False)
        app.config.setdefault('OIDC_OPENID_REALM', None)

        # config for resource servers
        app.config.setdefault('OIDC_RESOURCE_CHECK_AUD', True)

        self.client_secrets = app.config['OIDC']

    def add_callback_route(self, app):
        app.route('/oidc_callback')(self._oidc_callback)

    def add_request_decorators(self, app):
        # app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self):
        # g.oidc_id_token = None
        return self.authenticate_or_redirect()

    def openid_config(self, issuer):
        """
        Retrieve OpenID configuration for the specified issuer
        """

        config = self._config.setdefault(issuer, {})

        if not issuer:
            raise Exception('Unknown issuer {}'.format(issuer))

        if 'authorization_endpoint' not in config:

            self._config[issuer].update(requests.get(
                '{}/.well-known/openid-configuration'.format(issuer)).json())

            if 'userinfo_endpoint' in self._config[issuer]:
                self.client_secrets['userinfo_uri'] = (
                    self._config[issuer]['userinfo_endpoint'])

        return config

    def get_user(self, id_token):
        return self.app.extensions['security'].datastore.find_user(
            issuer_id=id_token['iss'],
            subject_id=id_token['sub'])

    def find_user(self, user_info):
        return self.app.extensions['security'].datastore.find_user(
            email=user_info['email'])

    def create_user(self, id_token, user_info):
        user_datastore = self.app.extensions['security'].datastore
        user = user_datastore.create_user(
            issuer_id=id_token['iss'],
            subject_id=id_token['sub'],
            email=user_info['email'],
            name=user_info.get('name'))
        user_datastore.commit()
        return user

    def get_or_create_user(self, id_token, user_info):
        print(user_info)

        user = self.get_user(id_token)

        if not user:
            user = self.find_user(user_info)

        if not user:
            user = self.create_user(id_token, user_info)

        return user

    # XXX overriding parent class

    def _set_cookie_id_token(self, id_token):
        super(OIDCClient, self)._set_cookie_id_token(id_token)

        if id_token is None:
            logout_user()

        else:
            user = self.get_or_create_user(id_token, self.user_getinfo([
                'email', 'name']))

            print('login_user', user, user.email)
            login_user(user)

            print('current_user', current_user)

    @cache(g, attr='_oidc_userinfo')
    def _retrieve_userinfo(self, access_token=None):

        try:
            _, content = self.authorized_request(
                access_token,
                self.client_secrets['userinfo_uri'])

        except ExpiredIDToken as err:
            logger.debug(str(err))

        else:
            return json.loads(str(content, 'utf-8'))

    def authorized_request(self, access_token, url):
        http = httplib2.Http()

        if access_token is None:
            return self.authorize(http).request(url)

        return http.request(url, 'POST', urlencode({
            'access_token': access_token}))

    def authorize(self, http):
        credentials = self.credentials_from_id_token()
        return credentials.authorize(http)

    def credentials_from_id_token(self):
        try:
            return OAuth2Credentials.from_json(
                self.credentials_store[g.oidc_id_token['sub']])

        except KeyError as e:
            raise ExpiredIDToken(e)

    def require_login(self, func):

        @wraps(func)
        def decorated_view(*args, **kwargs):

            if request.method in EXEMPT_METHODS:
                return func(*args, **kwargs)

            if current_app.login_manager._login_disabled:
                return func(*args, **kwargs)

            if not current_user.is_authenticated:

                if not self.disabled:

                    if getattr(g, 'oidc_id_token', None) is None:
                        return self.redirect_to_auth_server(request.url)

                return current_app.login_manager.unauthorized()

            return func(*args, **kwargs)

        return decorated_view
