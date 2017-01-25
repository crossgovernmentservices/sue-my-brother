from functools import wraps

from flask import current_app, redirect, request, session
from oic import rndstr
from oic.oic.message import EndSessionRequest
from werkzeug.exceptions import BadRequest


def authenticate(view_fn):

    @wraps(view_fn)
    def wrapper(*args, **kwargs):

        if _reauthentication_necessary():

            current_app.logger.info(
                'Redirecting to {idp} for authentication'.format(
                    idp=current_app.config['OIDC_CLIENT']['issuer']))

            return _authenticate()

        return view_fn(*args, **kwargs)

    return wrapper


def _reauthentication_necessary():
    return session.get('id_token') is None


def _authenticate():

    session.update({
        'destination': request.url,
        'state': rndstr(),
        'nonce': rndstr()
    })

    return redirect(_authentication_request())


def _authentication_request():
    client = current_app.extensions['oidc_client'].client
    auth_req = client.construct_AuthorizationRequest(
        request_args={
            'client_id': client.client_id,
            'response_type': 'code',
            'scope': ['openid', 'profile'],
            'redirect_uri': client.registration_response['redirect_uris'][0],
            'state': session['state'],
            'nonce': session['nonce'],
            'kc_idp_hint': session.get(
                'idp_hint', request.args.get('idp_hint')),
            'login_hint': session.get('email_address'),
            'claims': {
                'id_token': {
                    'email': None,
                    'name': None
                },
                'userinfo': {
                    'email': {'essential': True},
                    'name': {'essential': True}
                }
            }
        }
    )

    return auth_req.request(client.authorization_endpoint)


def logout(view_fn):
    current_app.extensions['oidc_client'].logout_view = view_fn

    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        id_token_jwt = session['id_token_jwt']

        if not _is_logout_redirect_callback():
            current_app.logger.info('Clearing session')
            session.clear()

            url = _provider_logout_url(id_token_jwt)
            if url:
                current_app.logger.info('Logging out of IDP')
                return redirect(url, 303)

        return view_fn(*args, **kwargs)

    return wrapper


def _is_logout_redirect_callback():
    state = request.args.get('state')
    is_redirect = state is not None

    if is_redirect and state != session.pop('end_session_state'):
        raise BadRequest('Mismatched state')

    return is_redirect


def _provider_logout_url(id_token_jwt):
    client = current_app.extensions['oidc_client']
    endpoint = client.client.provider_info.get('end_session_endpoint')
    logout_urls = client.client_registration_info['post_logout_redirect_uris']

    if not endpoint:
        return None

    session['end_session_state'] = rndstr()

    end_session_request = EndSessionRequest(
        id_token_hint=id_token_jwt,
        post_logout_redirect_uri=logout_urls[0],
        state=session['end_session_state'])

    return end_session_request.request(endpoint)
