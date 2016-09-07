# Sue My Brother

Dummy app to integrate with various GaaP services


## Dependencies

### GOV.UK Notify

You will need a [Notify account](https://www.notifications.service.gov.uk/)

Create an API key, and make a note of the key and your Service ID.

Create a file in the project directory, called `notify.env`, replacing
<your-api-key> with your API key, etc.

```
GOVUK_NOTIFY_BASE_URL=https://api.notifications.service.gov.uk
GOVUK_NOTIFY_API_KEY=<your-api-key>
GOVUK_NOTIFY_SERVICE_ID=<your-service-id>
```

Next, set up a couple of templates:

Email template
```
Dear ((plaintiff)),

Your lawsuit against your brother ((defendant)) has been accepted and is now
being brought to court.

You will receive an update when your suit has been adjudicated.
```

Make a note of the template ID.

Text message template
```
Your brother ((plaintiff)) is suing you for the terrible thing that you did. You
know what I'm talking about. That thing.
```

Make a note of the template ID.

Add the following lines to `notify.env`:
```
GOVUK_NOTIFY_TEMPLATE_ID_ACCEPT=<your-email-template-id>
GOVUK_NOTIFY_TEMPLATE_ID_SMS=<your-sms-template-id>
```

### GOV.UK Pay

You will need a Pay account - currently you will need to request this via their
[govuk-pay Slack channel](https://ukgovernmentdigital.slack.com/messages/govuk-pay/)

Create an API key, and create a file in the project directory called `pay.env`:

```
GOVUK_PAY_BASE_URL=https://publicapi.pymnt.uk
GOVUK_PAY_API_KEY=<your-api-key>
```

### OIDC login

User authentication is delegated to an OIDC Provider, for example Google
Accounts.

You need to register this app as a client with your chosen provider and get a
client ID and a client secret.

Create a file in the project directory called `oidc.env`:

```
OIDC_ISSUER=<url-of-oidc-provider>
OIDC_CLIENT_ID=<your-client-id>
OIDC_CLIENT_SECRET=<your-client-secret>
```

If you are authenticating with Google Accounts, you can add the following line:

```
OIDC_GOOGLE_APPS_DOMAIN=<your-google-apps-domain>
```

## Quickstart

```
git clone https://github.com/crossgovernmentservices/sue-my-brother

pip install -r requirements.txt

python manage.py db upgrade

python manage.py add_users

eval "$(python manage.py set_env)"

python manage.py install_all_govuk_assets

python manage.py runserver_ssl
```
