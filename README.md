# sue-my-brother
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

Make a not of the template ID.

Add the following lines to `notify.env`:
```
GOVUK_NOTIFY_TEMPLATE_ID_ACCEPT=<your-email-template-id>
GOVUK_NOTIFY_TEMPLATE_ID_SMS=<your-sms-template-id>
```

## Quickstart

```
git clone https://github.com/crossgovernmentservices/sue-my-brother

pip install -r requirements.txt

python manage.py db upgrade

python manage.py add_users

eval "$(python manage.py set_env)"

python manage.py runserver
```
