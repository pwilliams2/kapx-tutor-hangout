import json
import datetime
from google.appengine.api.datastore_errors import BadValueError

from google.appengine.runtime.apiproxy_errors import OverQuotaError
import jsonpickle

import tutor_hangouts_api as hapi
from apiclient import discovery
from utils import JSONEncoder, autolog
from lib.base import BaseHandler
from models.models import *


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


def assign_available_tutors(avail_tutors_list, subjects_list):
    """ Assign the tutors in the avail_ttutors_list to the  subjects
    :param avail_tutors_list: available tutors and their subjects
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

                try:
                    subject.put()
                except:
                    OverQuotaError
                autolog('Over Quota Error, bypassing for now')


def update_subjects():
    '''Update the subjects table to reflect the availability of the current tutor'''

    subjects_list = HangoutSubjects.query().fetch()

    # Retrieve Available Tutors and their subjects
    avail_tutors_list = TutorSubjects().query().fetch()

    if not 'items' in avail_tutors_list:  # There are no tutors available
        autolog('no avail_tutors_list')
        for subject in subjects_list:  # Set all subjects to unavailable
            subject.is_available = False
            subject.gid = None
            try:
                subject.put()
            except:
                OverQuotaError
            autolog('Over Quota Error, bypassing for now')
    else:
        autolog('avail_tutors_list has tutors %s' % avail_tutors_list)
        assign_available_tutors(avail_tutors_list, subjects_list)


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
    """ Update the TutorHangoutSessions store  """

    def get(self):
        """ Get the list of TutorHangoutSessions """
        return TutorHangoutSessions.query().fetch()


    def post(self):
        """ """
        autolog("updating tutor hangout session")
        tutor_id = self.request.get('tutorId')
        gid = self.request.get('gid')

        if self.request.get('exit'):
            """ The session ended, update the session end"""
            autolog("Updating session end")
            session = TutorHangoutSessions.query(TutorHangoutSessions.tutor_id == tutor_id
                                                 and TutorHangoutSessions.gid == gid).fetch(1)
            if not session:
                autolog(
                    'TutorHangoutSession was not found: tutor_id {%s}, gid{%s}' % (tutor_id, gid))
            else:
                now = datetime.datetime.now()
                delta = now - session[0].start
                session[0].end = now
                session[0].duration = delta.total_seconds() / 60  # minutes
                session[0].put()
        else:  # Create new TutorHangoutSession
            autolog("Creating new session")
            ho_session = TutorHangoutSessions(
                subject=self.request.get('subjects'),
                tutor_id=tutor_id,
                tutor_name=self.request.get('tutorName'),
                gid=gid,
                duration=None,
                participant_id=self.request.get('studentId'),
                participant_name=self.request.get('studentName')
            )
            ho_session.put()


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


class SurveyHandler(BaseHandler):
    def get(self):
        """ Retrieve TutorSurveys  """
        surveys = TutorSurveys().query().fetch()
        return self.response.out.write(surveys)

    def post(self):
        """ Post surveys  """
        try:
            survey = TutorSurveys(subject=self.request.get('subject'),
                              tutor_id=self.request.get('tutor_id'),
                              tutor_name=self.request.get('tutor_name'),
                              knowledge=float(self.request.get('knowledge')),
                              communications=float(self.request.get('communications')),
                              overall=float(self.request.get('overall')),
                              gid=self.request.get('gid'),
                              comments=self.request.get('comments'))
            out = survey.put()
            self.response.out.write(out)
        except BadValueError, e:
            print 'e ', e
            autolog('BadValueError on Tutor Survey Insert: ' + str(e))
            self.response.out.write('BadValueError on Tutor Survey Insert:' + str(e))
        except ValueError, e:
            autolog('ValueError on Tutor Survey Insert.')
            self.response.out.write('ValueError on Tutor Survey Insert:' + str(e))


class MainPage(BaseHandler):
    def get(self):
        self.render_template('views/index.html')


class SessionsPage(BaseHandler):
    def get(self):
        """ Get the list of TutorHangoutSessions """
        sessions = TutorHangoutSessions.query().fetch()

        template_data = {'sessions_query': sessions}
        self.render_template('views/sessions_report.html', **template_data)


