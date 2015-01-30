import uuid
from google.appengine.ext import ndb


class ClientApplication(ndb.Model):

    @classmethod
    def _get_kind(cls):
        # Renamed from `App` to prevent confusion between
        # request_handler.app being a reference to the WSGI Application
        return 'App'

    app_id = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    client_code = ndb.StringProperty()
    users = ndb.JsonProperty()
    domains = ndb.JsonProperty()
    domain_verification = ndb.BooleanProperty('dv')
    allow_localhost = ndb.BooleanProperty(default=True)
    private_key = ndb.StringProperty()
    private_key_verification = ndb.BooleanProperty('pkv')
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def create(cls, name, users, domains, client_code, app_id=None,
               private_key=None, domain_verification=False, allow_localhost=False,
               private_key_verification=False):
        if app_id is None:
            app_id = uuid.uuid4().hex
        if private_key is None:
            private_key = uuid.uuid4().hex

        app = cls(id=app_id)
        app.app_id = app_id
        app.name = name
        app.client_code = client_code
        app.users = users
        app.domains = domains
        app.domain_verification = domain_verification
        app.allow_localhost = allow_localhost
        app.private_key = private_key
        app.private_key_verification = private_key_verification

        app.put()

        return app


class Event(ndb.Model):
    app_id = ndb.StringProperty()
    event_name = ndb.StringProperty()
    event_data = ndb.TextProperty()
    user_data = ndb.TextProperty()
    session_data = ndb.TextProperty()
    environment_data = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    client_code = ndb.StringProperty(required=False)


class User(ndb.Model):
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    salt = ndb.StringProperty()


class LogEmail(ndb.Model):
    sender = ndb.StringProperty(required=True)
    to = ndb.StringProperty(required=True)
    subject = ndb.StringProperty(required=True)
    body = ndb.TextProperty()
    when = ndb.DateTimeProperty()


class WebHook(ndb.Model):
    event_name = ndb.StringProperty(required=True)
    client_code = ndb.StringProperty(required=True)
    hook_id = ndb.StringProperty(required=True)
    request_url = ndb.StringProperty(required=False)
    request_username = ndb.StringProperty(required=False)
    request_password = ndb.StringProperty(required=False)
    request_method = ndb.StringProperty(required=False)
    timeout = ndb.IntegerProperty(required=False)
    retries = ndb.IntegerProperty(required=False)

    @classmethod
    def fetch_by_client(cls, client_code, event_name=None):
        """Queries for a list of `WebHook`s for a `client_code`, and optionally filtering by `event_name`

        Args
            :param client_code: The client's whose events to fetch
            :type client_code: basestring
            :param event_name: Optional event name filter
            :type event_name: basestring

        Returns
            :return: A query containing the list of matched items
            :rtype: ndb.Query
        """
        hooks = cls.query(WebHook.client_code == client_code)
        if event_name:
            hooks = hooks.filter(WebHook.event_name == event_name)
        return hooks


