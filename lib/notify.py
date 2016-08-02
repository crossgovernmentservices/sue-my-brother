# -*- coding: utf-8 -*-
"""
GOV.UK Notify client Flask extension
"""

from notifications_python_client import NotificationsAPIClient


class Notification(object):

    def __init__(self, client, template_id):
        self.client = client
        self.data = {'template': template_id}

    def _send(self, endpoint, recipient, personalisation):

        if self.client.disabled:
            return

        self.data['to'] = recipient

        if personalisation:
            self.data['personalisation'] = personalisation

        try:
            return self.client.post(endpoint, data=self.data)

        except Exception as e:
            print("POST {}{} failed".format(self.client.base_url, endpoint))
            raise e

    def send_sms(self, recipient, **personalisation):
        return self._send('/notifications/sms', recipient, personalisation)

    def send_email(self, recipient, **personalisation):
        return self._send('/notifications/email', recipient, personalisation)


class Notify(NotificationsAPIClient):

    def __init__(self, app=None):
        self.base_url = None
        self.client_id = None
        self.secret = None
        self.disabled = False
        self.notifications = {}

        if app:
            self.init_app(app)

    def init_app(self, app):
        self._app = app
        config = dict(app.config['GOVUK_NOTIFY'])
        self.base_url = config.get('base_url')
        self.client_id = config.get('client_id')
        self.secret = config.get('secret')
        self.disabled = config.get('disabled', False)

        assert self.base_url, "Missing GOVUK_NOTIFY base_url setting"
        assert self.client_id, "Missing GOVUK_NOTIFY client_id setting"
        assert self.secret, "Missing GOVUK_NOTIFY secret setting"

        for name, template_id in config.get('templates', {}).items():
            self.notifications[name] = Notification(self, template_id)

    def __getitem__(self, key):
        return self.notifications[key]
