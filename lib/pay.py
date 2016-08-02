import uuid

from dateutil.parser import parse as parse_date
import requests
from requests.auth import AuthBase


def payment_reference():
    return str(uuid.uuid4())


class PaymentMixin(object):

    def update_from_json(self, json):
        self.provider = json['payment_provider']
        self.status = json['state']['status']
        self.finished = json['state']['finished']
        self.status_msg = json['state'].get('message', '')
        self.description = json['description']
        self.created = parse_date(json['created_date'])
        self.url = json['_links']['self']['href']
        self.next_url = json['_links']['next_url']['href']


class TokenAuth(AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer {}'.format(self.token)
        return r


class PaymentError(Exception):
    pass


class PaymentNotFound(PaymentError):
    pass


class PayAPIAuthFailed(PaymentError):
    pass


class PaymentCreationError(PaymentError):

    def __init__(self, response):
        self.status_code = response.status_code
        json = response.json()
        self.error_code = json['code']
        self.error_field = json.get('field')
        self.description = json['description']

    def __str__(self):
        return self.description


class Pay(object):

    def __init__(self, app=None):
        self.base_url = None
        self.api_key = None
        self._payment_class = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        config = dict(app.config['GOVUK_PAY'])
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')

        assert self.base_url, "Missing GOVUK_PAY base_url setting"
        assert self.api_key, "Missing GOVUK_PAY api_key setting"

        if not app.extensions:
            app.extensions = {}

        app.extensions['govuk_pay'] = self

    def payment_class(self, cls):
        self._payment_class = cls
        return cls

    def create_payment(self, amount, desc, return_url, ref=None):

        if ref is None:
            ref = payment_reference()

        r = requests.post(
            '{}/v1/payments'.format(self.base_url),
            auth=TokenAuth(self.api_key),
            headers={'Accept': 'application/json'},
            json={
                'amount': amount,
                'reference': ref,
                'description': desc,
                'return_url': return_url})

        if r.status_code in (400, 422, 500):
            raise PaymentCreationError(r)

        payment = self._payment_class(
            reference=ref,
            amount=amount,
            description=desc)
        payment.update_from_json(r.json())
        payment.save()

        return payment

    def update_status(self, payment):

        r = requests.get(
            payment.url,
            auth=TokenAuth(self.api_key),
            headers={'Accept': 'application/json'})

        if r.status_code == 401:
            raise PayAPIAuthFailed()

        if r.status_code == 404:
            raise PaymentNotFound()

        if r.status_code == 500:
            raise PaymentError(r.json()['description'])

        json = r.json()
        payment.update(
            status=json['state']['status'],
            finished=json['state']['finished'],
            status_msg=json['state'].get('message', ''))

        return payment
