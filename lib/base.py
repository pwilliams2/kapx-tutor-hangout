import logging
import os
import webapp2
import jinja2

from urlparse import urlparse

from google.appengine.api.app_identity import get_application_id

import config


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