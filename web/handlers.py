import json
import datetime

from google.appengine.ext import ndb

import tutor_hangouts_api as hapi
from apiclient import discovery
from utils import JSONEncoder, autolog
from lib.base import BaseHandler
from models.models import TutorSubjects, HangoutSubjects


def remove_stale_sessions():
    """ When a tutor closes their H-O, we need to remove them from the available subjects """
    autolog("remove_stale_sessions")
    now = datetime.datetime.now()
    del_list = TutorSubjects.query().fetch()
    keys = []
    for item in del_list:
        delta = now - item.last_modified
        if delta.total_seconds() > 60:
            keys.append(item.key)

    ndb.delete_multi(keys)


def assign_available_tutors(avail_tutors_list, service, subjects_list):
    """ Assign the tutors in the avail_ttutors_list to the  subjects
    :param avail_tutors_list: available tutors and their subjects
    :param service: service object
    :param subjects_list: the tutored subjects
    :return:
    """
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

                if avail_subject == subject.subject and tutor['participants_count'] < tutor['max_participants']:
                    subject.gid = tutor['gid']
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

                autolog('hs_body: %s: ' % json.loads(json.dumps(hs_body)))
                service.subjects().update(entityKey=subject_key, body=hs_body).execute()


def update_subjects():
    '''Update the subjects table to reflect the availability of the current tutor'''

    discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
    service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

    subjects_list = HangoutSubjects.query().fetch()

    # Retrieve Available Tutors and their subjects
    avail_tutors_list = service.tutor_subjects().list().execute()

    if not 'items' in avail_tutors_list:  # There are no tutors available
        autolog('no avail_tutors_list')
        for subject in subjects_list:  # Set all subjects to unavailable
            subject_key = subject.key.urlsafe()
            hs_body = {
                "is_available": False,
                "gid": None
            }
            service.subjects().update(entityKey=subject_key, body=hs_body).execute()
    else:
        autolog('avail_tutors_list has tutors %s' % avail_tutors_list)
        assign_available_tutors(avail_tutors_list, service, subjects_list)


class PublishHandler(BaseHandler):
    def post(self):
        self.publish_tutor()
        update_subjects()

    def get_tutor_subjects_entity_key(self):
        entity_key = self.request.get('entityKey')
        if not entity_key:
            ts_list = TutorSubjects.query(TutorSubjects.person_id == self.request.get('pid')).fetch(1, keys_only=True)

            if ts_list:  # Found an existing tutor person_id
                entity_key = ts_list[0].urlsafe()
        return entity_key


    def publish_tutor(self):
        """ Insert/update the subjects for which the tutor is available """

        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        count = int(self.request.get('count')) if self.request.get('count') else 0
        max = int(self.request.get('maxParticipants')) if self.request.get('maxParticipants') else 1

        tutor_body = {
            "person_id": self.request.get('pid'),
            "tutor_name": self.request.get('pName'),
            "gid": self.request.get('gid'),
            "subjects": self.request.get('subjects'),
            "participants_count": count,
            "max_participants": max
        }

        entity_key = self.get_tutor_subjects_entity_key()

        if entity_key:
            autolog("Updating tutor subject")
            output = service.tutor_subjects().update(entityKey=entity_key, body=tutor_body).execute()
        else:
            autolog("New tutor")
            output = service.tutor_subjects().insert(body=tutor_body).execute()

        self.response.out.write(JSONEncoder().encode(output))


class HeartbeatHandler(BaseHandler):
    """ Heartbeat of the tutor's hangout  """

    def get(self):
        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        ts_list = TutorSubjects.query(TutorSubjects.person_id == self.request.get('pid')).fetch()

        if not ts_list:  # hangout is no longer available
            pass
        else:  # Found an existing tutor person_id
            entity_key = ts_list[0].key.urlsafe()
            count = self.request.get("count") if self.request.get("count") else 1
            tutor_body = {
                "gid": self.request.get('gid'),
                "participants_count": count
            }
            output = service.tutor_subjects().update(entityKey=entity_key, body=tutor_body).execute()
            remove_stale_sessions()  # cleanup closed sessions
            update_subjects()  # Update available subjects
            return self.response.out.write(JSONEncoder().encode(output))


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
        """ Returns the list of subjects with available tutors """

        remove_stale_sessions()
        update_subjects()

        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        subjects = service.subjects().list(order='subject').execute()
        if subjects:
            return self.response.out.write(JSONEncoder().encode(subjects.get('items', [])))
        else:
            autolog("no subjects found")
            return [{}]


class MainPage(BaseHandler):
    def get(self):
        self.render_template('templates/student.html')
