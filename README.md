# Sue My Brother

Dummy app to integrate with various GaaP services

## Recommendation

It is possible to install libraries using other means but in this set up for sue-my-brother homebrew was used

### Homebrew

```
	/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

## Pre-requisites for sue-my-brother

### Python and pip

```
	brew install python3
	sudo easy_install pip

	python3 -m venv venv
	. venv/bin/activate

	pip install -r requirements.txt
```

## Pre-requisites for running sue-my-brother with a local [Dex](https://github.com/coreos/dex) instance

### Docker and Postgres

Download and install [Docker](https://docs.docker.com/engine/installation/)

Download and install [PostgresSQL](https://www.postgresql.org/download/)

### Append to bash_profile

```
export PATH=$PATH:/Applications/Postgres.app/Contents/Versions/9.5/bin
```

### Ruby

```
	gem install bundle
	rbenv install 2.2.0
	
```

## Dependencies

### GOV.UK Notify

You will need a [Notify account](https://www.notifications.service.gov.uk/)

Create an API key, and make a note of the key and your Service ID.

Create a file in the project directory, called `notify.env`, replacing
<your-api-key> with your API key, etc.

```
GOVUK_NOTIFY_BASE_URL=https://api.notifications.service.gov.uk
GOVUK_NOTIFY_SERVICE_URL=https://www.notifications.service.gov.uk
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
GOVUK_PAY_BASE_URL=https://publicapi.integration.pymnt.uk
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

update users.txt to add your log in details

python manage.py db upgrade

python manage.py add_users

eval "$(python manage.py set_env)"

./install_govuk_assets

```

If running against an active identity management service

```
python manage.py runserver_ssl
```

## Quickstart - running sue-my-brother against local instance of dex

```
git clone https://github.com/crossgovernmentservices/csd-identity-products.git

cd csd-identity-products/products/dex/docker-compose
docker-compose up
```

This will wait for connectors. Once it's doing so run this in another terminal:

```
docker exec -it dockercompose_overlord_1 /opt/dex/bin/dexctl --db-url postgres://user:password@postgres:5432/user?sslmode=disable set-connector-configs /opt/dex/connectors/connectors.json
```

This should result in IdP connectors being loaded.

Generate keys

```
docker exec -it dockercompose_overlord_1 /opt/dex/bin/dexctl --db-url postgres://user:password@postgres:5432/user?sslmode=disable new-client https://localhost:5443/oidc_callback
```

Copy and append output to oidc.env file in sue-my-brother directory,
2 keys to copy

```
DEX_APP_CLIENT_ID=<your-client-id>
DEX_APP_CLIENT_SECRET=<your-client-secret>
```

NB - you will need to replace DEX_APP with OIDC and add the following

```
OIDC_ISSUER=http://dex.example.com:5556
```

The hosts file will also need the following line added
```
0.0.0.0         dex.example.com
```

The environment variables will need to be updated (necessary whenever .env file is changed)

```
eval "$(python manage.py set_env)"
```

Start the website 
```
python manage.py runserver_ssl
```

### Test the website

```
https://localhost:5443/
```
