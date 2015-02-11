import json
import datetime

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine import runtime
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
    del_list = TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).fetch()

    if del_list and len(del_list) > 0:
        autolog('del_list')
        keys = []
        for item in del_list:
            delta = now - item.last_modified
            if delta.total_seconds() > 60:
                keys.append(item.key)

        if len(keys) > 0:
            autolog('deleting tutor keys ' % keys)
            ndb.delete_multi(keys)


def assign_available_tutors(avail_tutors, subjects_list):
    """ Assign the tutors in the avail_tutors_list to the  subjects
    :param avail_tutors_list: available tutors and their subjects
    :param subjects_list: the tutored subjects
    :return:
    """
    avail_subjects = []
    for tutor in avail_tutors:
        json_tutor_subjects = json.loads(tutor.subjects)
        for tutor_subject in json_tutor_subjects:
            subject = tutor_subject['subject']
            avail_subjects.append(subject)

        done = []  # Subjects that are already updated.
        if len(avail_subjects) == 0:  # No available tutors, so set all subjects to unavailable
            subjects = []
            for subject in subjects_list:
                if subject.subject in done:
                    continue
                subject.is_available = False
                subjects.append(subject)
            ndb.put_multi(subjects)
            break

        for avail_subject in avail_subjects:
            for subject in subjects_list:
                if subject.subject in done:
                    continue

                if avail_subject == subject.subject and tutor.participants_count < tutor.max_participants:
                    subject.gid = tutor.gid
                    subject.is_available = True

                    if avail_subject not in done:
                        done.append(avail_subject)
                else:
                    subject.is_available = False
                    subject.gid = ''

                try:
                    subject.put()
                except OverQuotaError, e:
                    autolog('Over Quota Error, bypassing for now: ' + str(e))


def update_subjects():
    '''Update the subjects table to reflect the availability of the current tutor'''

    subjects_list = HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).fetch()

    # Retrieve Available Tutors and their subjects
    avail_tutors = TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).fetch()

    if not avail_tutors:  # There are no tutors available
        autolog('No available tutors.')
        for subject in subjects_list:  # Set all subjects to unavailable
            subject.is_available = False
            subject.gid = None
            try:
                subject.put()
            except OverQuotaError, e:
                autolog('Over Quota Error, bypassing for now: ' + str(e))
    else:
        autolog('There are avail_tutors.')
        assign_available_tutors(avail_tutors, subjects_list)


def dump_json(a_list):
    if len(a_list) > 0:
        data = {
            "data": [item for item in a_list]
        }
        return JSONEncoder().encode(data)
        # return json.dumps(data)
    else:
        return {[]}


class PublishHandler(BaseHandler):
    def post(self):
        """ Post available tutor subjects
        :return: None
        """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.publish_tutor()
        update_subjects()


    def publish_tutor(self):
        """ Insert/update the subjects for which the tutor is available """

        try:
            ts = TutorSubjects.query(TutorSubjects.person_id == self.request.get('pid')).fetch(1)

            count = int(self.request.get('count')) if self.request.get('count') else 0
            max = int(self.request.get('maxParticipants')) if self.request.get('maxParticipants') else 1

            if ts:
                autolog("Updating tutor subject")
                ts[0].gid = self.request.get('gid')
                ts[0].subjects = self.request.get('subjects')
                ts[0].participants_count = count
                ts[0].max_participants = max
                ts_key = ts[0].put()
            else:
                autolog("New tutor")
                ts = TutorSubjects(parent=hapi.TUTOR_SUBJECTS_PARENT_KEY,
                                   person_id=self.request.get('pid'),
                                   subjects=self.request.get('subjects'),
                                   tutor_name=self.request.get('pName'),
                                   gid=self.request.get('gid'),
                                   max_participants=max,
                                   participants_count=count)
                ts_key = ts.put()
            self.response.out.write(ts_key)
        except Exception, e:
            autolog('msg: ' + str(e))


class HeartbeatHandler(BaseHandler):
    """ Heartbeat of the tutor's hangout  """

    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.response.headers['Content-Type'] = 'text/plain'

        # Search for the specified tutor id == pid
        ts_list = TutorSubjects.query(TutorSubjects.person_id == self.request.get('pid')).fetch()

        if not ts_list:  # hangout is no longer available
            pass
        else:  # Found an existing tutor person_id, then update the count
            entity_key = ts_list[0].key.urlsafe()
            count = self.request.get("count") if self.request.get("count") else 1
            ts_list[0].gid = self.request.get('gid')
            ts_list[0].participants_count = int(count)
            ts_key = ts_list[0].put()

        remove_stale_sessions()  # cleanup closed sessions
        update_subjects()  # Update available subjects
        self.response.set_status(200, 'ok')


class SessionHandler(BaseHandler):
    def get(self):
        """ List of sessions      """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        ths_list = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).fetch()

        data_list = []
        for session in ths_list:
            start_date = session.start.strftime('%Y-%m-%d %H:%M') if session.start else ''
            survey_id = session.survey_key.id() if session.survey_key else ''
            autolog('survey_id %s' % survey_id)
            duration = str('%10.2f' % session.duration) if session.duration else ''
            row_list = ['', session.tutor_name, session.participant_name, session.subject,
                        start_date, duration, survey_id]

            data_list.append(row_list)

        self.response.out.write(dump_json(data_list))


class SubscribeHandler(BaseHandler):
    """ Update the TutorHangoutSessions store  """

    def get(self):
        """ Get the list of TutorHangoutSessions """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).fetch()


    def post(self):
        """ Subscribe client for H-O session"""
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        autolog("updating tutor hangout session")
        tutor_id = self.request.get('tutorId')
        gid = self.request.get('gid')

        if self.request.get('exit'):
            """ The session ended, update the session end"""
            autolog("Updating session end")
            session = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(ndb.AND(
                TutorHangoutSessions.tutor_id == tutor_id, TutorHangoutSessions.gid == gid)).fetch(1)
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
            ho_session = TutorHangoutSessions(parent=hapi.TUTOR_SESSIONS_PARENT_KEY,
                                              subject=self.request.get('subjects'),
                                              tutor_id=tutor_id,
                                              tutor_name=self.request.get('tutorName'),
                                              gid=gid,
                                              duration=None,
                                              participant_id=self.request.get('studentId'),
                                              participant_name=self.request.get('studentName')
            )
            ho_key = ho_session.put()
            self.response.set_status(200)
            self.response.out.write(ho_key)


class SubjectsHandler(BaseHandler):
    def get(self):
        """ Returns the list of subjects with available tutors """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        remove_stale_sessions()
        update_subjects()

        # Build a service object for interacting with the API.
        discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (hapi.API_ROOT, hapi.API_NAME, hapi.VERSION)
        service = discovery.build(hapi.API_NAME, hapi.VERSION, discoveryServiceUrl=discovery_url)

        try:
            subjects = service.subjects().list(order='subject').execute()
            if subjects:
                return self.response.out.write(JSONEncoder().encode(subjects.get('items', [])))
            else:
                self.response.set_status(204)
                self.response.set_status_message('No subjects found')
                autolog("no subjects found")
                return None
        except runtime.DeadlineExceededError, e:
            autolog('Deadline Exceed Error: ' + str(e))
            return None


class SurveyHandler(BaseHandler):
    def get(self):
        """ Retrieve TutorSurveys  """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        student_id = self.request.get('student_id')
        gid = self.request.get('gid')

        if student_id and gid:  # A survey lookup
            surveys = TutorSurveys.query(
                ndb.AND(TutorSurveys.student_id == student_id, TutorSurveys.gid == gid)).fetch()
        else:
            surveys = TutorSurveys.query(ancestor=hapi.TUTOR_SURVEYS_PARENT_KEY).fetch()

        self.response.out.write(dump_json(surveys))

    def post(self):
        """ Post surveys  """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        student_id = self.request.get('student_id')
        gid = self.request.get('gid')

        if len(student_id) == 0 or len(gid) == 0:
            self.response.set_status(500, 'Missing student id or gid values')
            return False

        survey = TutorSurveys.query(ndb.AND(TutorSurveys.student_id == student_id, TutorSurveys.gid == gid)).fetch()

        try:
            if survey:
                survey[0].knowledge = float(self.request.get('knowledge'))
                survey[0].communications = float(self.request.get('communications'))
                survey[0].overall = float(self.request.get('overall'))
                survey[0].comments = self.request.get('comments')
                survey[0].student_id = student_id
                survey[0].student_name = self.request.get('student_name')
                survey[0].tutor_name = self.request.get('tutor_name')
                s_key = survey[0].put()
                self.response.out.write(s_key)
            else:
                survey = TutorSurveys(parent=hapi.TUTOR_SURVEYS_PARENT_KEY,
                                      subject=self.request.get('subject'),
                                      student_id=student_id,
                                      tutor_name=self.request.get('tutor_name'),
                                      student_name=self.request.get('student_name'),
                                      knowledge=float(self.request.get('knowledge')),
                                      communications=float(self.request.get('communications')),
                                      overall=float(self.request.get('overall')),
                                      gid=gid,
                                      comments=self.request.get('comments'))
                survey_key = survey.put()
                self.update_session_with_survey(gid, student_id, survey_key)
                self.response.out.write(survey_key)
        except BadValueError, e:
            self.response.set_status(500, 'BadValueError on Tutor Survey Insert.' + str(e))
            autolog('BadValueError on Tutor Survey Insert: ' + str(e))
            self.response.out.write('BadValueError on Tutor Survey Insert:' + str(e))
        except ValueError, e:
            self.response.set_status(500, 'ValueError on Tutor Survey Insert.' + str(e))
            autolog('ValueError on Tutor Survey Insert.')
        except Exception, e:
            self.response.set_status(500, 'Exception on Tutor Survey Insert.' + str(e))
            autolog('Exception on Tutor Survey Insert.')
            self.response.out.write('Exception on Tutor Survey Insert:' + str(e))


    def update_session_with_survey(self, gid, student_id, survey_key):
        """ Update the Hangout Session with a survey key
        :param survey_key:
        :return:
        """

        session = TutorHangoutSessions.query(
            ndb.AND(TutorHangoutSessions.participant_id == student_id, TutorHangoutSessions.gid == gid)).fetch()
        if session:
            session[0].survey_key = survey_key
            session[0].put()
            return True
        else:
            return False