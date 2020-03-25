# Web Hook Notifications

There are 3 subscription types supported:

- New - notification for any new credential (i.e. newly registered organization) of a specific type
- Stream - any updates for a specific stream - organization (by Topic) and type
- Topic - any updates for a specific organization (Topic)

Interested parties must first register, which creates an ID and password they use to manage their subscriptions.  They can then add and remove subscriptions.

They must also provide a REST endpoint for the notifications - they can provide an endpoint with their scubscription and/or an endpoint with each separate subscription.

The REST endpoints to manage subscriptions are listed in the Aries VCR Swagger page, if you are running locally this is at `htp://localhost:8080/api/`

## Setting up a Test Listener

A test "echo" endpoint is available in this project at https://github.com/hyperledger/aries-vcr/starter-kits/credential-registry/server/echo-service - you can run this service in Play With Docker or play With VON and then you can use this service as the endpoint for the web hooks.  Alternately this service will start up by default with you start Aries VCR using the `./manage build` and `./manage start` docker scripts.

Create a session on PWD or PWV and run the following commands:

```
git clone https://github.com/hyperledger/aries-vcr.git
cd aries-vcr/starter-kits/credential-registry/server/echo-service
./run_docker.sh
```

This will expose the echo service on a public endpoint, that will be visible to Aries VCR callbacks.  If you click on the port `8000` link at the top of the page, it will display the public service name - add `/api/echo` to get the name of the web service, for example:

```
http://ip172-18-0-6-bnomr08t969000ca90fg-8000.direct.labs.play-with-docker.com/api/echo
```

You can POST to this URL with a JSON body, and the body contents will be printed in the console, for example:

```
curl -X POST -d "{\"hello\": \"world\"}" http://ip172-18-0-6-bnomr08t969000ca90fg-8000.direct.labs.play-with-docker.com/api/echo
```

Alternately you can run the echo service on your localhost and expose the port publicly using ngrok.

Note that this service exposes two other endpoints that are useful for testing web hooks:

- `/api/error` - will always respond with `500 Server Error`
- `/api/rando` - will randomly respond with either HTTP `200` or `500` status

## Registration

You must register to setup an identity (ID and password) in order to create and manage subscriptions.  Your subscritions will be protected with your ID and password.  In your own Aries VCR deployment you can modify the security scheme to integrate with an external security provider, such as KeyCloak or &etc ...

The registration endpoint is `/hooks/register` and you must provide the following data:

```
{
  "email": "ian@anon-solutions.ca",
  "org_name": "Anon Solutions Inc",
  "target_url": "http://localhost:8000/api/echo",
  "hook_token": "some-random-string-0987654321",
  "credentials": {
    "username": "anon",
    "password": "anon-password-randomstuff"
  }
}
```

- email - the email address responsible for the subscription
- org_name - the name of the subscribing organization
- target_url - the target url for web hooks (note this is optional and can be provided per-subscription)
- hook_token - the token that Aries VCR will include with all web hook notifications (you provide, we send)
- username - the identity of the subscription owner (must be provided for all subscription maintenance)
- password - the password for the subscription owner identity (must be provided for all subscription maintenance)

Note that the subscription process will return the following, including an updated username:

```
{
  "reg_id": 1,
  "email": "ian@anon-solutions.ca",
  "org_name": "Anon Solutions Inc",
  "target_url": "http://localhost:8000/api/echo",
  "hook_token": "some-random-string-0987654321",
  "registration_expiry": "2020-03-10",
  "credentials": {
    "username": "anon-gza4lvbsjomrmjolufm6u2xcy2e7o6oz"
  }
}
```

Note that:

- the username is updated to include a random string
- there is an expiry date on the registration (3 months) - the registration (or any subscription) must be updated before the expiry date (it can be updated with the same values) or the registration and subscriptions will be de-activated

For any subsequent operations (view or update registration, view or update subscriptions, etc.) you need to provide the username and password (in the example above `anon-user-kcmpmt7ijt0rltpfnqqh4tlezwy4g2nu` and `anon-password-randomstuff`).

## Maintaining Subscriptions

The endpoint to add new subscriptions is `/hooks/registration/{username}/subscriptions`, you need to provide the following:

```
{
  "subscription_type": "New",
  "topic_source_id": "BC1234567",
  "credential_type": "registration.registries.ca",
  "target_url": "http://localhost:8000/api/echo",
  "hook_token": "some-random-string-0987654321"
}
```

- subscription_type - `New`, `Stream` or `Topic`
- topic_source_id - Topic (for example organization number), required for subscription types `Stream` and `Topic`
- credential_type - schema name for the credential, e.g. `registration.registries.ca` - required for subscription type `Stream`
- target_url - (optional) - if not provided the registration value will be used
- hook_token - (optional) - if not provided the registration value will be used

The endpoint will return:

```
{
  "sub_id": 1,
  "owner": "anon-user-kcmpmt7ijt0rltpfnqqh4tlezwy4g2nu",
  "subscription_type": "New",
  "topic_source_id": "BC1234567",
  "target_url": "http://localhost:8000/api/echo",
  "hook_token": "some-random-string-0987654321",
  "last_sent_date": null,
  "last_error_date": null,
  "error_count": 0,
  "subscription_expiry": null
}
```

Note that Aries VCR will do a test call to the target_url, to verify that the endpoint is valid.  (It does this for a subscription event, but not a registration event.)

You can view your subscriptions at `/hooks/registration/{username}/subscriptions`, or `/hooks/registration/{username}/subscriptions/{id}` (where `id` is the `sub_id` returned from the subscription service call).

The last 4 attributes are set when web hooks are sent (or attempted) to the target url:

- last_sent_date - date/time of last successful web hook
- last_error_date - date/time of last un-successful web hook
- error_count - the number of cumulative errors since the last successful transmission (reset to zero on a successful web hook)
- subscription_expiry - date the subscription was expired (or `null` if the subscription is active)

Note that the subscription will be auto-expired if there are too many unsuccessful web hooks.

You can re-activate the subscription by sending a `PUT` request for the subscription.  (It doesn't need to update any fields, a `PUT` will automatically reset the error_count and subscription_expiry fields.)

## Receiving Web Hooks

For any matching event, Aries VCR will send a POST request to the target URL with the following payload:

```
{
    "data": {
        "corp_num": "BC1188712",
        "credential_json": {
            "attributes": {
                "effective_date": "2018-12-01T05:00:00+00:00",
                "entity_name": "JAFFSONS HOLDINGS LTD.",
                "entity_name_assumed": "",
                "entity_name_assumed_effective": "",
                "entity_name_effective": "2018-12-01T05:00:00+00:00",
                "entity_name_trans": "",
                "entity_name_trans_effective": "",
                "entity_status": "ACT",
                "entity_status_effective": "2018-12-01T05:00:00+00:00",
                "entity_type": "BC",
                "expiry_date": "",
                "extra_jurisdictional_registration": "",
                "home_jurisdiction": "BC",
                "reason_description": "Filing:AMALV",
                "registered_jurisdiction": "",
                "registration_date": "2018-12-01T05:00:00+00:00",
                "registration_expiry_date": "",
                "registration_id": "BC1188712",
                "registration_renewal_effective": ""
            },
            "cred_def_id": "6qnvgJtqwK44D8LFYnV5Yf:3:CL:10:default",
            "schema_name": "registration.registries.ca"
        },
        "credential_type": "registration.registries.ca",
        "id": 374
    },
    "subscription": {
        "credential_type": null,
        "hook_token": "some-random-string-0987654321",
        "id": 1,
        "owner": "anon-user-gza4lvbsjomrmjolufm6u2xcy2e7o6oz",
        "subscription_type": "New",
        "target_url": "http://ip172-18-0-6-bnomr08t969000ca90fg-8000.direct.labs.play-with-docker.com/api/echo",
        "topic_id": "BC1234567"
    }
}
```

The `data` is the attached credential (the format will depend on the credential type) and the `subscription` will identify the subscription for which the hook was generated.

Note that when adding or updating a subscription, we send a web hook with payload `{"subscription": {"test": "test"}}` - the hook should respond to this with a `200` status.

## Monitoring

You can monitor the rabbitmq process at `http://localhost:15672/` (for a setup running on localhost).

## How does it Work???

There are a few settings that configure how the web hooks work:

```
# authenticate REST hook services so only the subscriber can view/update their subscriptions
AUTHENTICATION_BACKENDS = ["subscriptions.icatrestauth.IcatAuthBackend"]

# wrapper function that delivers the web hook (passes the task to a rabbitmq worker)
HOOK_DELIVERER = "subscriptions.tasks.deliver_hook_wrapper"

# data model that triggers hooks to be sent - when a new record is added it triggers the hook services to run
HOOK_CUSTOM_MODEL = "subscriptions.models.CredentialHook"

# for hook events, checks the credential against the subscriptions to see which hooks to fire
HOOK_FINDER = "subscriptions.hook_utils.find_and_fire_hook"

# how to monitor for events - look for "created" events
HOOK_EVENTS = {
    # 'any.event.name': 'App.Model.Action' (created/updated/deleted)
    "hookable_cred.added": "subscriptions.HookableCredential.created+"
}
```

... and to configure rabbitmq and celery:

```
# celery settings
CELERY_BROKER_HEARTBEAT = 0  # see https://github.com/celery/celery/issues/4817

CELERY_BROKER_URL = "pyamqp://{}:{}@{}//".format(
    os.environ.get("RABBITMQ_USER"),
    os.environ.get("RABBITMQ_PASSWORD"),
    os.environ.get("RABBITMQ_SVC_NAME", "rabbitmq"),
)

# database backend for retrieving task results
CELERY_TASK_BACKEND = "db+postgresql://{}:{}@{}/{}".format(
    os.environ.get("DATABASE_USER"),
    os.environ.get("DATABASE_PASSWORD"),
    os.environ.get("DATABASE_SERVICE_NAME"),
    os.environ.get("DATABASE_NAME"),
)

# custom hook settings
# max retries for http errors
HOOK_RETRY_THRESHOLD = os.environ.get("HOOK_RETRY_THRESHOLD", 3)
# number of seconds to wait between retries
HOOK_RETRY_DELAY = os.environ.get("HOOK_RETRY_DELAY", 5)
# max errors on a subscription before "expiring" the subscription
HOOK_MAX_SUBSCRIPTION_ERRORS = os.environ.get("HOOK_MAX_SUBSCRIPTION_ERRORS", 10)
```
