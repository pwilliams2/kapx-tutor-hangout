#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import logging

import webapp2
import tutor_hangouts_api as hapi
from google.appengine.ext import ndb

from apiclient import discovery

from models.models import HangoutSubjects, TutorHangoutSessions, TutorSubjects
from utils import JSONEncoder, autolog, LogPage


SUBJECTS_PARENT_KEY = ndb.Key("Entity", 'subjects_root')
TUTOR_SUBJECTS_PARENT_KEY = ndb.Key("Entity", 'tutor_subjects_root')
TUTOR_SESSIONS_PARENT_KEY = ndb.Key("Entity", 'tutor_sessions_root')


def handle_404(request, response, exception):
    logging.exception(exception)
    response.write('Oops! I could swear this page was here!')
    response.set_status(404)


def handle_500(request, response, exception):
    logging.exception(exception)
    response.write('A server error occurred!')
    response.set_status(500)


def load(self):
    autolog("loading subjects")
    HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                    subject="Business",
                    isAvailable=False).put()

    HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                    subject="Technology",
                    isAvailable=False).put()

    HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                    subject="General Math",
                    isAvailable=False).put()

    HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                    subject="Calculus",
                    isAvailable=False).put()

    HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                    subject="Science",
                    isAvailable=False).put()

    HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                    subject="Writing",
                    isAvailable=False).put()


class BaseHandler(webapp2.RequestHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

    def post(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

    def handle_exception(self, exception, debug):
        # Log the error.
        logging.exception(exception)

        # Set a custom message.
        self.response.write('An error occurred: %s' % (exception))

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)


class PingHandler(BaseHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        autolog("Pinghandler")

        # Print some JSON
        self.response.out.write('{"PingHandler":"Alive..."}\n')


class PublishHandler(BaseHandler):
    def post(self):
        BaseHandler.post(self)
        # TODO: Update the TutorSubjects ndb, then use that to update the HangoutSubjects
        self.update_tutor()

    def get_entity_key(self):
        entity_key = self.request.get('entityKey')
        if not entity_key:
            ts_list = TutorSubjects.query(TutorSubjects.person_id == self.request.get('pid')).fetch(1, keys_only=True)

            if ts_list:  # Found an existing tutor person_id
                entity_key = ts_list[0].urlsafe()
        return entity_key

    def update_tutor(self):
        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        tutor_body = {
            "person_id": self.request.get('pid'),
            "tutor_name": self.request.get('pName'),
            "gid": self.request.get('gid'),
            "subjects": self.request.get('subjects')
        }

        entity_key = self.get_entity_key()

        if entity_key:
            autolog("Updating tutor subject")
            output = service.tutor_subjects().update(entityKey=entity_key, body=tutor_body).execute()
        else:
            autolog("New tutor")
            output = service.tutor_subjects().insert(body=tutor_body).execute()

        self.response.out.write(JSONEncoder().encode(output))


class SubscribeHandler(BaseHandler):
    def update_session(self):
        autolog("updating tutor hangout session")
        tutor_session = TutorHangoutSessions(parent=TUTOR_SESSIONS_PARENT_KEY)
        tutor_session.subjects = self.request.get('subjects')
        tutor_session.person_id = self.request.get('pid')
        tutor_session.name = self.request.get('pName')
        tutor_session.gid = self.request.get('gid')
        tutor_session.put()


class SubjectsHandler(BaseHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        # self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        subjects = service.subjects().list(order='subject').execute()
        if subjects:
            return self.response.out.write(JSONEncoder().encode(subjects))
        else:
            autolog("no subjects found")
            return [{}]


application = webapp2.WSGIApplication([
                                          ('/', SubjectsHandler),
                                          ('/publishsubjects', PublishHandler),
                                          ('/heartbeat', PingHandler),
                                          ('/logs', LogPage),
                                      ], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500
