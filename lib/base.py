import logging
from urlparse import urlparse

import webapp2
import jinja2
from google.appengine.api.app_identity import get_application_id

import config
import utils


jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(config.base_path))


class BaseHandler(webapp2.RequestHandler):

    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        # return jinja_environment.get_jinja2(app=self.app)
        return jinja2.get_jinja2(app=self.app)

    def render_template(self, template_file, mime_type='text/html', **template_data):
        logging.info(mime_type)
        application_id = get_application_id()
        template_data.update({
            'application_id': application_id,
            'url': self.request.url,
            'base_url': urlparse(self.request.url).scheme + "://" + urlparse(self.request.url).netloc
        })
        self.response.headers['Content-Type'] = mime_type
        template = jinja_environment.get_template(template_file)
        self.response.out.write(template.render(**template_data))

    def get_required_value(self, some_value, some_name=None):
        """ Return valid value or raise and error; use for required values.
        :param request:
        :return:
        """

        if not some_value and some_name:
            utils.autolog("Value: is missing or not valid %s" % some_name)
            raise ValueError("Value: %s is missing or not valid" % some_name)
        elif not some_value:
            utils.autolog("Value: is missing or not valid")
            raise ValueError("Value: is missing or not valid")
        else:
            return some_value