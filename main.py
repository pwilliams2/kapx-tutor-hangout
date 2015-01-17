#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#from google.appengine.ext.webapp import util
from google.appengine.ext import ndb

import logging
import webapp2
import models.models as models

DEFAULT_TUTOR_HANGOUTS_NAME = 'tutor_hangouts'

def tutor_hangouts_key(tutor_hangouts_name=DEFAULT_TUTOR_HANGOUTS_NAME):
    """Constructs a Datastore key for a Tutor entity."""
    return ndb.Key('Tutor_Hangouts', tutor_hangouts_name)

class BaseHandler(webapp2.RequestHandler):
    def handle_exception(self, exception, debug):
        # Log the error.
        logging.exception(exception)

        # Set a custom message.
        self.response.write('An error occurred.')

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)

def handle_404(request, response, exception):
    logging.exception(exception)
    response.write('Oops! I could swear this page was here!')
    response.set_status(404)

def handle_500(request, response, exception):
    logging.exception(exception)
    response.write('A server error occurred!')
    response.set_status(500)


class MainHandler(BaseHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        # Print some JSON
        self.response.out.write('{"mainHandler":"Submit Clicked!"}\n')

class ReservationHandler(BaseHandler):
    def get(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.

         # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        # Print some JSON

        tutor = models.Tutor(parent=tutor_hangouts_key(DEFAULT_TUTOR_HANGOUTS_NAME))
        tutor.subjects = self.request.get('subjects')
        tutor.id = self.request.get('pid')
        tutor.name = self.request.get('pName')
        tutor.gid = self.request.get('gid')

        tutor.put()
       # self.response.out.write('{"rsvpHandler":"Submit Clicked!"}\n')

        #self.response.out.write("pid: " + tutor.id + "\n")


application = webapp2.WSGIApplication([
        ('/', MainHandler),
        ('/subjects', ReservationHandler)
    ], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500