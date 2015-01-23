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

import json
import logging

import webapp2
from google.appengine.ext import ndb

from apiclient import discovery
from models.models import HangoutSubjects, TutorHangoutSessions, TutorSubjects
from utils import JSONEncoder, autolog
from tutor_hangouts_api import API, API_ROOT, VERSION

SUBJECTS_PARENT_KEY = ndb.Key("Entity", 'subjects_root')
TUTOR_SUBJECTS_PARENT_KEY = ndb.Key("Entity", 'tutor_subjects_root')
TUTOR_SESSIONS_PARENT_KEY = ndb.Key("Entity", 'tutor_sessions_root')

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

class PingHandler(BaseHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        autolog("Pinghandler")

        # Print some JSON
        self.response.out.write('{"PingHandler":"Alive..."}\n')

class ReservationHandler(BaseHandler):
    def get(self):
        # We set the same parent key to ensure each entirty
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.

        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        self.updatesubject()
        self.redirect(self.request.referer)

    def updatesubject(self):
        logging.info('updatesubject')

        subjects = self.request.get('subjects')
        tutor_person_id = self.request.get('pid')
        tutor_name = self.request.get('pName')
        hangout_id = self.request.get('gid')

        sel_subjects = json.loads(subjects)
        json_string = json.dumps(sel_subjects,sort_keys=True,indent=4, encoding="utf-8")

        for ho_subject in sel_subjects:  # Get selected tutor subject(s)
            jsonobj = json.loads(JSONEncoder().encode(ho_subject))
            input_subject = jsonobj['subject']
            state = jsonobj['state']  #boolean for subject availability
            logging.info('subject: {s}, state {s}', (jsonobj['subject'], jsonobj['state']))

            # Find the existing subject and update it's availability to TRUE
            subjects_list = HangoutSubjects.query(ancestor=SUBJECTS_PARENT_KEY).filter(HangoutSubjects.subject == input_subject).fetch()

            for subject in subjects_list:
                subject.isAvailable = state
                subject.put()


    def updatetutor(self):
        logging.info("updatetutor")
        tutor = TutorSubjects(parent=TUTOR_SUBJECTS_PARENT_KEY)
        tutor.subjects = self.request.get('subjects')
        tutor.id = self.request.get('pid')
        tutor.name = self.request.get('pName')
        tutor.put()

    def updatesession(self):
        logging.info("updatesession")
        tutor_session = TutorHangoutSessions(parent=TUTOR_SESSIONS_PARENT_KEY)
        tutor_session.subjects = self.request.get('subjects')
        tutor_session.id = self.request.get('pid')
        tutor_session.name = self.request.get('pName')
        tutor_session.gid = self.request.get('gid')
        tutor_session.put()

class SessionInfoHandler(BaseHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        # subjects = HangoutSubjects.query(ancestor=SUBJECTS_PARENT_KEY).order(HangoutSubjects.subject).fetch()
        subjects = self.get_subjects()

        if not subjects:
            load(self)  # hydrate subject model
            subjects = self.get_subjects()

        self.response.out.write(JSONEncoder().encode(subjects))

    def get_subjects(self):
        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (API_ROOT, API, VERSION)
        service = discovery.build(API, VERSION, discoveryServiceUrl=discovery_url)

        response = service.subjects().list(order='subject').execute()
        if response:
            return response.get('items', [])
        else:
            autolog("no subjects found")
            return [{}]

application = webapp2.WSGIApplication([
        ('/', SessionInfoHandler),
        ('/addsubjects', ReservationHandler),
        ('/heartbeat', PingHandler)
    ], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500


# def main():
#     # Build a service object for interacting with the API.
#     api_root = 'https://kx-tutor-hangout-app.appspot.com/_ah/api'
#     api = 'tutorhangouts'
#     version = 'v1'
#     discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (api_root, api, version)
#     service = build(api, version, discoveryServiceUrl=discovery_url)
#
#     # Fetch all greetings and print them out.
#     response = service.subjects().list.execute()
#     # response = service.greetings().list().execute()
#     pprint.pprint(response)
#
#      # Fetch a single greeting and print it out.
#     # response = service.greetings().get(id='9001').execute()
#     # pprint.pprint(response)
#
# if __name__ == '__main__':
#   main()