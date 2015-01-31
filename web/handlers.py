import json
import os
from google.appengine.ext import ndb
import jinja2

import tutor_hangouts_api as hapi
from apiclient import discovery
from utils import JSONEncoder, autolog
from lib.base import BaseHandler

from models.models import TutorHangoutSessions, TutorSubjects, HangoutSubjects


# Jinja environment instance necessary to use Jinja views.
# jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
#                                autoescape=True)



class PublishHandler(BaseHandler):
    def post(self):
        self.update_tutor()
        self.update_subjects()

    def get_tutor_subjects_entity_key(self):
        entity_key = self.request.get('entityKey')
        if not entity_key:
            ts_list = TutorSubjects.query(TutorSubjects.person_id == self.request.get('pid')).fetch(1, keys_only=True)

            if ts_list:  # Found an existing tutor person_id
                entity_key = ts_list[0].urlsafe()
        return entity_key

    def update_subjects(self):
        '''
        Update the subjects table to reflect the availability of the current tutor
        :return:
        '''

        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        subjects_list = HangoutSubjects.query().fetch()

        # Retrieve Available Tutors and their subjects
        avail_tutors_list = service.tutor_subjects().list().execute()
        # subjects_list = service.subjects().list().execute()
        # subjects = subjects_list['items']
        avail_tutors = avail_tutors_list['items']
        avail_subjects = []

        for tutor in avail_tutors:
            json_tutor_subjects = json.loads(tutor['subjects'])
            for tutor_subject in json_tutor_subjects:
                subject = tutor_subject['subject']
                avail_subjects.append(subject)

        done = []  # Subjects that are already updated.
        for avail_subject in avail_subjects:
            for subject in subjects_list:
                subject_key = subject.key.urlsafe()

                if subject.subject in done:
                    continue

                if avail_subject == subject.subject:
                    subject.gid = self.request.get('gid')
                    subject.is_available = True

                    if avail_subject not in done:
                        done.append(avail_subject)
                else:
                    subject.is_available = False
                    subject.gid = ''

                hs_body = {
                    "subject": subject.subject,
                    "is_available": subject.is_available,
                    "gid": subject.gid
                }

                print 'hs_body: %s: ' % json.loads(json.dumps(hs_body))
                service.subjects().update(entityKey=subject_key, body=hs_body).execute()

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

        entity_key = self.get_tutor_subjects_entity_key()

        if entity_key:
            autolog("Updating tutor subject")
            output = service.tutor_subjects().update(entityKey=entity_key, body=tutor_body).execute()
        else:
            autolog("New tutor")
            output = service.tutor_subjects().insert(body=tutor_body).execute()

        self.response.out.write(JSONEncoder().encode(output))


class SubscribeHandler(BaseHandler):
    def get(self):
        self.response.out.write("Subscribed")
        # autolog("updating tutor hangout session")
        # tutor_session = TutorHangoutSessions(parent=TUTOR_SESSIONS_PARENT_KEY)
        # tutor_session.subjects = self.request.get('subjects')
        # tutor_session.person_id = self.request.get('pid')
        # tutor_session.name = self.request.get('pName')
        # tutor_session.gid = self.request.get('gid')
        # tutor_session.put()


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


class MainPage(BaseHandler):
    def get(self):
        self.render_template('templates/index.html')
