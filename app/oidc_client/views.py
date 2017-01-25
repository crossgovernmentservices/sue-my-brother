from flask import current_app, redirect, request, session
from oic.oauth2.exception import MissingEndpoint
from oic.oic.message import AuthorizationResponse


def callback():
    current_app.logger.info('Handling authentication callback')

    code, state = _parse_auth_response()

    current_app.logger.info('Exchanging authz code for access and id tokens')

    id_token, access_token = _get_tokens(code, state)

    current_app.logger.info('Requesting userinfo')

    userinfo = _get_userinfo(id_token, state)

    session.update({
        'id_token': id_token.to_dict(),
        'id_token_jwt': id_token.to_jwt(),
        'access_token': access_token
    })

    if userinfo:
        session['userinfo'] = userinfo.to_dict()

    current_app.logger.info('Redirecting to {destination}'.format(
        destination=session.get('destination')))

    return redirect(session.pop('destination'))


def _parse_auth_response():
    client = current_app.extensions['oidc_client'].client
    auth_response = client.parse_response(
        AuthorizationResponse,
        info=request.query_string.decode('utf-8'),
        sformat='urlencoded')

    state = auth_response['state']

    if state != session.pop('state'):
        raise ValueError("The 'state' parameter does not match")

    return auth_response['code'], state


def _get_tokens(code, state):
    client = current_app.extensions['oidc_client'].client
    args = {
        'code': code,
        'redirect_uri': client.registration_response['redirect_uris'][0],
    }

    token_response = client.do_access_token_request(
        state=state,
        request_args=args,
        authn_method=client.registration_response.get(
            'token_endpoint_auth_method', 'client_secret_basic'))

    id_token = token_response['id_token']
    if id_token['nonce'] != session.pop('nonce'):
        raise ValueError("The 'nonce' parameter does not match")

    return id_token, token_response['access_token']


def _get_userinfo(id_token, state):
    client = current_app.extensions['oidc_client'].client

    try:
        userinfo = client.do_user_info_request(method='POST', state=state)

    except MissingEndpoint:
        return None

    if userinfo['sub'] != id_token['sub']:
        raise ValueError(
            "The userinfo 'sub' does not match the id token 'sub'")

    if 'email' not in userinfo:
        current_app.logger.warn('IDP did not supply email claim in userinfo')

        if 'email' in id_token:
            userinfo['email'] = id_token['email']

        else:
            current_app.logger.warn(
                'IDP did not supply email claim in id token')

            if 'email_address' in session:
                userinfo['email'] = session['email_address']

            else:
                current_app.logger.warn('User email address unknown')

    return userinfo
