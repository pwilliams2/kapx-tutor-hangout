import json

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb

import utils
from data import DataHandler
import tutor_hangouts_api as hapi
from utils import JSONEncoder, autolog
from lib.base import BaseHandler
from models.models import TutorHangoutSessions, TutorSurveys


class SurveyHandler(BaseHandler):
    def get(self):
        """ Retrieve TutorSurveys  """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        student_id = self.request.get('student_id')
        gid = self.request.get('gid')
        survey_url = self.request.get('survey_key')

        if survey_url:
            survey_key = ndb.Key(urlsafe=survey_url)
            if survey_key:
                survey = survey_key.get()
                if survey:
                    return self.response.out.write(JSONEncoder().encode(survey))
        elif student_id and gid:  # A survey lookup
            surveys = TutorSurveys.query(
                ndb.AND(TutorSurveys.student_id == student_id, TutorSurveys.gid == gid)).fetch()
        else:
            surveys = TutorSurveys.query(ancestor=hapi.TUTOR_SURVEYS_PARENT_KEY).order(
                -TutorSurveys.create_date).fetch()

        return self.response.out.write(utils.dump_json(surveys))


    def post(self):
        """ Post surveys  """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        student_id = self.request.get('student_id')
        gid = self.request.get('gid')

        if len(student_id) == 0 or len(gid) == 0:
            self.response.set_status(500, 'Missing student id or gid values')
            return False

        avail_subjects = []
        if self.request.get('subject'):
            subjects_list = json.loads(self.request.get('subject'))
            for tutor_subject in subjects_list:
                subject = str(tutor_subject['subject'])
                avail_subjects.append(subject)

        if avail_subjects:
            inp_subject = avail_subjects[0]
        else:
            tutor_subjects = DataHandler.get_tutor_subjects(None, gid)
            autolog(tutor_subjects)
            if tutor_subjects:
                inp_subject = tutor_subjects[0].subjects[0]

        # Retrieve current surveys to determine if it's an update or insert
        survey_list = TutorSurveys.query(ancestor=hapi.TUTOR_SURVEYS_PARENT_KEY).filter(
            ndb.AND(TutorSurveys.student_id == student_id, TutorSurveys.gid == gid)).fetch()
        try:
            if survey_list:
                survey = survey_list[0]
                survey.knowledge = float(self.request.get('knowledge'))
                survey.communications = float(self.request.get('communications'))
                survey.overall = float(self.request.get('overall'))
                survey.comments = self.request.get('comments')
                survey.student_id = student_id
                survey.subject = inp_subject
                survey.student_name = self.request.get('student_name')
                survey.tutor_name = self.request.get('tutor_name')
                survey_key = survey.put()
                self.response.out.write(survey_key.urlsafe())
            else:
                survey = TutorSurveys(parent=hapi.TUTOR_SURVEYS_PARENT_KEY,
                                      subject=inp_subject,
                                      student_id=student_id,
                                      tutor_name=self.request.get('tutor_name'),
                                      student_name=self.request.get('student_name'),
                                      knowledge=float(self.request.get('knowledge')),
                                      communications=float(self.request.get('communications')),
                                      overall=float(self.request.get('overall')),
                                      gid=gid,
                                      comments=self.request.get('comments'))
                survey_key = survey.put()
                self.response.out.write(survey_key.urlsafe())

            self.update_session_with_survey(gid, student_id, survey_key.urlsafe())
        except BadValueError, e:
            self.response.set_status(500, 'BadValueError on Tutor Survey Insert.' + str(e))
            autolog('BadValueError on Tutor Survey Insert: ' + str(e))
            self.response.out.write('BadValueError on Tutor Survey Insert:' + str(e))
        except ValueError, e:
            self.response.set_status(500, 'ValueError on Tutor Survey Insert.' + str(e))
            autolog('ValueError on Tutor Survey Insert.')
        except Exception, e:
            self.response.set_status(500, 'Exception on Tutor Survey Insert.' + str(e))
            autolog('Exception on Tutor Survey Insert: %s' % str(e))
            self.response.out.write('Exception on Tutor Survey Insert:' + str(e))


    def update_session_with_survey(self, gid, student_id, survey_key):
        """ Update the Hangout Session with a survey key
        :param survey_key:
        :return:
        """

        # Client could have multiple sessions for the same HangoutId.  Assign survey to the latest open (no end date)
        # session.
        # try:
        session = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(
            ndb.AND(TutorHangoutSessions.participant_id == student_id, TutorHangoutSessions.gid == gid,
                    TutorHangoutSessions.duration <= 0.0)).fetch()

        if session:
            autolog('updating session.survey_key')
            session[0].survey_key = survey_key
            session[0].put()
            return True
        else:
            autolog('session not found')
            return False
