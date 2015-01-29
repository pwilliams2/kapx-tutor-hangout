import base64
import logging
import webapp2
import webob.exc
import jsonpickle
# import requests

import sys
import traceback
from webapp2_extras import jinja2

from google.appengine.api.app_identity import get_application_id
from google.appengine.api import taskqueue, memcache

from models.core import ClientApplication
import config


def jinja2_factory(app):
    j = jinja2.Jinja2(app)
    j.environment.filters.update({
        # Set filters.
        # ...
    })
    j.environment.globals.update({
        # Set global variables.
        'getattr': getattr,
        'str': str
    })
    j.environment.loader.searchpath[:] = ['views']
    j.environment.tests.update({
        # Set test.
        # ...
    })
    return j


def handle_error(request, response, exception):
    exc_type, exc_value, exc_tb = sys.exc_info()

    c = {
        'exception': str(exception),
        'url': request.url,
    }

    if request.app.config.get('send_mail_developer') is not False:
        # send email
        subject = "[{}] ERROR {}".format(config.environment.upper(), config.app_name)

        lines = traceback.format_exception(exc_type, exc_value, exc_tb)

        message = '<strong>Type:</strong> ' + exc_type.__name__ + "<br />" + \
                  '<strong>Description:</strong> ' + c['exception'] + "<br />" + \
                  '<strong>URL:</strong> ' + c['url'] + "<br />" + \
                  '<strong>Traceback:</strong> <br />' + '<br />'.join(lines)

        email_body_path = "emails/error.txt"
        if c['exception'] is not 'Error saving Email Log in datastore':
            template_val = {
                "app_name": config.app_name,
                "message": message,
            }

            email_body = jinja2.get_jinja2(factory=jinja2_factory, app=webapp2.get_app()).render_template(
                email_body_path, **template_val)
            email_url = webapp2.uri_for('taskqueue-send-email')

            for dev in config.developers:
                taskqueue.add(url=email_url, params={
                    'to': dev[1],
                    'subject': subject,
                    'body': email_body,
                    'sender': config.contact_sender,
                })

    status_int = hasattr(exception, 'status_int') and exception.status_int or 500
    template = config.error_templates[status_int]
    t = jinja2.get_jinja2(factory=jinja2_factory, app=webapp2.get_app()).render_template(template, **c)
    logging.error(str(status_int) + " - " + str(exception))
    response.write(t)
    response.headers['Content-Type'] = "text/html"
    response.set_status(status_int)


def appid_authentication(func):
    """Auth decorator for app_id based authentication

    :type func: __builtin__.function
    """
    def check_app_id(handler, *args, **kwargs):
        """Auth callback to validate the requested app id

        :param handler: The Request Handler
        :type handler: BaseHandler
        """
        try:
            # query string or form data
            app_id = get_app_id(handler)

            if not app_id:
                handler.abort(401, comment="Missing app_id in request")

            handler.client_app = ClientApplication.get_by_id(app_id)

            if not handler.client_app:
                handler.abort(403, comment="No app configured for app_id '{0}'".format(app_id))

            handler.client_code = handler.client_app.client_code
        except Exception, e:
            logging.exception(e)
            raise
        return func(handler, *args, **kwargs)
    return check_app_id


def get_app_id(handler):
    """Helper function to get the app_id from the request

    This wrapper checks in
    1. Request parameters (query string or form data)
    2. json encoded request body for an app_id key

    Args
        :param handler: The Request Handler
        :type handler: BaseHandler

    Returns
        :return: The app id if found in the request
        :rtype: str|None
    """
    # query string or form data
    app_id = handler.request.get('app_id')

    if not app_id:
        if 'json' in handler.request.content_type:
            # POST / PUT with json encoded body
            data = jsonpickle.decode(handler.request.body)
            app_id = data.get('app_id')

    return app_id if app_id else None


def get_http_auth_credentials(handler):
    """Gets the encoded authorization parameter from the request if present

    :param handler: The Request Handler
    :type handler: BaseHandler
    :return:
    :rtype: str|None
    """
    request = handler.request
    auth_header = request.headers.get('Authorization', '')
    logging.info('Authorization: %s', auth_header)

    if not auth_header.startswith('Basic '):
        return None
    return auth_header.replace('Basic ', '')


def get_client_from_auth(encoded_auth_header, client_code):
    pass
    """Gets the client requested based upon the encoded auth header value

    :param encoded_auth_header: The base64 encoded auth header
    :type encoded_auth_header: str
    :param client_code: The client code from the request to match on
    :type client_code: str
    :return: The auth'd client
    :rtype: dict|None
    """
    # memcache for speed on repeated calls for auth.
    # Use the base64 encoded credentials as the key

    # client = memcache.get(encoded_auth_header)
    # if not client:
    #     username, password = base64.b64decode(encoded_auth_header).split(':')
    #     client = get_client_from_identity(client_code, username, password)
    #     if client:
    #         memcache.set(encoded_auth_header, client, 3000)
    # return client if client else None


def client_context(func):
    """Auth decorator for HTTP Auth w/client credentials

    :type func: __builtin__.function
    """
    def check_client(handler, *args, **kwargs):
        """Auth callback

        :param handler: The Request Handler
        :type handler: BaseHandler
        """

        auth_header = get_http_auth_credentials(handler)
        if not auth_header:
            logging.error("No Authorization header or bad value GOT: '%'", auth_header)
            handler.abort(401)

        try:
            client = get_client_from_auth(auth_header, kwargs['client_code'])
            if not client:
                handler.abort(403)
            handler.client_code = client['client_code']
        except Exception, e:
            logging.exception(e)
            raise
        return func(handler, *args, **kwargs)
    return check_client


def app_id_or_http_auth(func):
    """Auth decorator that allows an app_id or HTTP Basic auth

    Args
        :param func: Handler method to call
        :type func: __builtin__.function

    Returns
        :return: the wrapped function
        :rtype: __builtin__.function
    """
    def gotta_check_em_all(handler, *args, **kwargs):

        # Flag to determine if it should be a 401 (no credentials) or 403 (invalid credentials)
        found_credentials = False

        # app_id first
        try:
            app_id = get_app_id(handler)
            logging.info("Request app_id '%s'", app_id)

            if app_id:
                found_credentials = True
                client_app = ClientApplication.get_by_id(app_id)
                logging.info("Matched client app '%s'", client_app.name)

                if client_app:
                    handler.client_app = client_app
                    handler.client_code = handler.client_app.client_code
                    # Happy path, had auth_id and matched a client app!
                    return func(handler, *args, **kwargs)
        except Exception as e:
            logging.error("Error during app_id auth %s", e.message)

        # then HTTP Basic
        try:
            auth_header = get_http_auth_credentials(handler)
            if auth_header:
                found_credentials = True
                client = get_client_from_auth(auth_header, kwargs['client_code'])
                if client:
                    handler.client_code = client['client_code']
                    # Happy path, HTTP Auth matched someone!
                    return func(handler, *args, **kwargs)
        except Exception as e:
            logging.error("Error during HTTP Auth %s", e.message)

        # finally fail
        if found_credentials:
            handler.abort(403, explanation="Invalid Credentials")
        handler.abort(401, explanation="No app_id or Authorization header present")

    return gotta_check_em_all


def get_client_from_identity(client_code, username, password):
   pass
   """Executes the actual request to the hook url"""
    # try:
    #
    #     request_auth = (username, password)
    #     auth_url = config.identity_base_url + "/api/client/" + client_code
    #     response = requests.get(auth_url, auth=request_auth)
    #     response.raise_for_status()
    #     client = response.json()
    #     return client
    #
    # except Exception as e:
    #     logging.error("Unable to authenticate client against %s", config.identity_base_url)
    #     logging.exception(e)
    #     return None


class BaseHandler(webapp2.RequestHandler):

    def __init__(self, request=None, response=None):
        super(BaseHandler, self).__init__(request, response)
        self.client_code = None
        self.client_app = None

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(factory=jinja2_factory, app=self.app)

    def render_template(self, template_file, mime_type='text/html', **template_data):
        logging.info(mime_type)
        logging.info(template_file)
        application_id = get_application_id()
        template_data.update({
            'application_id': application_id,
            'url': self.request.url,
            'host_url': self.request.host_url,
            'uri_for': self.uri_for,
        })
        self.response.headers['Content-Type'] = mime_type
        self.response.out.write(self.jinja2.render_template(template_file, **template_data))

    def get_current_client(self):
        return self.client_code


class JsonHandler(BaseHandler):
    """Handles setting Content-Type to application/json and returning of consistently formatted JSON results."""
    def __init__(self, request, response):
        self.request_data = None
        super(JsonHandler, self).__init__(request, response)

    def dispatch(self):
        try:
            self.response.content_type = 'application/json'
            result = super(JsonHandler, self).dispatch()
            if result is not None:
                self.api_success(result)
        except webob.exc.WSGIHTTPException as e:
            # catch self.abort() properly
            logging.exception(e)
            self.response.set_status(e.code)
            error = dict(error=getattr(e, 'explanation', 'Unknown Error'))
            self.response.write(jsonpickle.encode(error, unpicklable=False))
            return
        except Exception, e:
            if not self.response.status:
                self.error(500)
            self.handle_exception(e, False)

    def __render_json__(self, data):
        self.response.write(jsonpickle.encode(data, unpicklable=False))

    def api_success(self, data=None, status=200):
        if data is None:
            # No content and no response
            self.response.status = 204
        else:
            self.response.status = status
            self.__render_json__(data)

    def set_location_header(self, model):
        self.response.headers["Location"] = "{0}/{1}".format(self.request.path, model.key().id())

    def _data(self):
        if self.request_data is None:
            data_string = self.request.body
            self.request_data = jsonpickle.decode(data_string)
        return self.request_data