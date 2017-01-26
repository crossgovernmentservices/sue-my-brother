from flask import url_for
from oic.oic import Client
from oic.oic.message import RegistrationRequest
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

from app.oidc_client import views  # noqa
from app.oidc_client.decorators import authenticate, logout  # noqa


class OIDCClient(object):

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        self._app = app

        if not app.extensions:
            app.extensions = {}

        app.extensions['oidc_client'] = self

        config = app.config.get('OIDC_CLIENT', {})

        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        client.provider_config(config['issuer'])

        config['redirect_uris'] = [self._init_redirect_uri(app)]

        client.store_registration_info(RegistrationRequest(**config))

        self.client = client
        self.client_registration_info = config
        self.logout_view = None

    def _init_redirect_uri(self, app):
        app.add_url_rule('/oidc_callback', 'oidc_callback', views.callback)

        with app.app_context():
            return url_for('oidc_callback', _external=True)
