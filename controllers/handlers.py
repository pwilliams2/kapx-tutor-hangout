import json
import datetime
from collections import deque

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine import runtime
from google.appengine.ext import ndb

import tutor_hangouts_api as hapi
from utils import JSONEncoder, autolog
from lib.base import BaseHandler
from models.models import TutorSubjects, TutorHangoutSessions, HangoutSubjects, TutorSurveys


tutorQueue = deque()  # FIFO q to serve subscribers


def remove_stale_sessions():
    """ When a tutor closes their H-O, we need to remove them from the available subjects """
    autolog("remove_stale_sessions")
    now = datetime.datetime.now()
    del_list = get_tutor_subjects()

    if del_list and del_list:
        autolog('del_list')
        keys = []
        for item in del_list:
            delta = now - item.last_modified
            if delta.total_seconds() > 60:
                keys.append(item.key)

        if keys:
            autolog('deleting tutor keys ' % keys)
            ndb.delete_multi(keys)


def assign_available_tutors(subjects_list):
    """ Assign the tutors in the avail_tutors_list to the subjects in the subjects_list
    :param subjects_list: the tutored subjects
    :return:
    """

    try:
        autolog('tutorQueue size %s' % str(len(tutorQueue)))

        size = len(tutorQueue)
        for subject in subjects_list:  # Get next an available tutor in q
            i = 0
            subject.is_available = False
            subject.gid = ''

            while tutorQueue and i < size:
                i += 1
                current_tutor = tutorQueue.pop()

                tutor_list = get_tutor_subjects(current_tutor.tutor_id, current_tutor.gid)
                if tutor_list:
                    tutor = tutor_list[0]

                    if subject.subject in tutor.subjects and tutor.participants_count < tutor.max_participants:
                        autolog('Tutor match found for: %s' % subject)
                        subject.gid = tutor.gid  # Assign a tutor to the subject
                        subject.is_available = True
                        subject.put()
                        tutorQueue.appendleft(tutor)  # Put the tutor back in the q
                        break
                    else:
                        tutorQueue.appendleft(tutor)  # Put the tutor back in the q
            subject.put()
        return True
    except OverQuotaError, e:
        autolog('Over Quota Error, bypassing for now: ' + str(e))
        raise


def update_subjects():
    """ Update the subjects table to reflect the availability of the current tutor """

    subjects_list = HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).fetch()

    # Retrieve Available Tutors and their subjects
    avail_tutors = get_tutor_subjects()

    if not avail_tutors:  # There are no tutors available
        autolog('No available tutors.')
        for subject in subjects_list:  # Set all subjects to unavailable
            try:
                subject.is_available = False
                subject.gid = None
                subject.put()
            except OverQuotaError, e:
                autolog('Over Quota Error, bypassing for now: ' + str(e))
    else:
        autolog('There are avail_tutors.')
        assign_available_tutors(subjects_list)


def dump_json(a_list):
    if a_list:
        data = {
            "data": [item for item in a_list]
        }
        return JSONEncoder().encode(data)
        # return json.dumps(data)
    else:
        return [{}]


def get_tutor_subjects(tutor_id=None, gid=None):
    """ Return the tutor
    :param tutor_id:
    :param gid:
    :return:
    """

    if tutor_id and gid:
        return TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).filter(
            ndb.AND(TutorSubjects.tutor_id == tutor_id, TutorSubjects.gid == gid)).fetch(1)
    elif tutor_id:
        return TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).filter(
            TutorSubjects.tutor_id == tutor_id).fetch(1)
    elif gid:
        return TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).filter(
            TutorSubjects.gid == gid).fetch(1)
    else:
        return TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).fetch()


def remove_tutor_from_queue(tutor_id):
    """  When a tutor starts a session with a client (student), remove them from avail queue
    :param tutor_id:
    :return:
    """

    size = len(tutorQueue)
    i = 0
    while i < size:
        i += 1
        tutor = tutorQueue.pop()
        if tutor.tutor_id == tutor_id:
            return True
        else:
            tutorQueue.appendleft(tutor)  # Put it back if it doesn't match
    return False


class HangoutRequestHandler(BaseHandler):
    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        url = 'https://talkgadget.google.com/hangouts/_/'  # gid is appended below at run-time
        gid = self.request.get('gid')
        subject = self.request.get('subject')
        autolog("HangoutRequestHandler url %s, %s, %s" % (url, gid, subject))
        uri = url + gid + '?gd=' + subject

        return self.redirect(str(uri))


class HeartbeatHandler(BaseHandler):
    """ Heartbeat of the tutor's hangout  """

    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.response.headers['Content-Type'] = 'text/plain'

        # Search for the specified tutor id == pid
        ts_list = get_tutor_subjects(self.request.get('pid'))

        if not ts_list:  # hangout is no longer available
            pass
        else:  # Found an existing tutor tutor_id, then update the count
            count = self.request.get("count") if self.request.get("count") else 1
        ts_list[0].gid = self.request.get('gid')
        ts_list[0].participants_count = int(count)
        ts_list[0].put()

        remove_stale_sessions()  # cleanup closed sessions
        update_subjects()  # Update available subjects
        self.response.set_status(200, 'ok')


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
            tutor = get_tutor_subjects(self.request.get('pid'), self.request.get('gid'))

            count = int(self.request.get('count')) if self.request.get('count') else 0
            max_participants = int(self.request.get('maxParticipants')) if self.request.get('maxParticipants') else 1
            inp_subjects = self.request.get('subjects') if self.request.get('subjects') else ''

            avail_subjects = []
            if inp_subjects:
                subjects_list = json.loads(inp_subjects)
                for tutor_subject in subjects_list:
                    subject = str(tutor_subject['subject'])
                    avail_subjects.append(subject)

            if tutor:
                tutor = tutor[0]
                autolog("Updating tutor subject")
                tutor.gid = self.request.get('gid')
                tutor.subjects = avail_subjects
                tutor.participants_count = count
                tutor.max_participants = max_participants
                ts_key = tutor.put()

                autolog("Tutor subjects: %s" % str(tutor.subjects))
                if len(tutorQueue) == 0:
                    tutorQueue.appendleft(tutor)
            else:
                autolog("New tutor")
                tutor = TutorSubjects(parent=hapi.TUTOR_SUBJECTS_PARENT_KEY,
                                      tutor_id=self.request.get('pid'),
                                      subjects=avail_subjects,
                                      tutor_name=self.request.get('pName'),
                                      gid=self.request.get('gid'),
                                      max_participants=max_participants,
                                      participants_count=count)
                ts_key = tutor.put()

                # Add the tutor to the FIFO queue.
                tutorQueue.appendleft(tutor)
            self.response.out.write(ts_key.urlsafe())
        except Exception, e:
            autolog('msg: ' + str(e))


class SessionHandler(BaseHandler):
    def get(self):
        """ List of sessions      """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        ths_list = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).fetch()
        return self.response.out.write(dump_json(ths_list))


class SubscribeHandler(BaseHandler):
    """ Update the TutorHangoutSessions store  """

    def get(self):
        """ Get the list of TutorHangoutSessions """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        ths_list = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).fetch()
        return self.response.out.write(dump_json(ths_list))

    def post(self):
        """ Subscribe client for H-O session"""
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        autolog("updating tutor hangout session")
        tutor_id = self.request.get('tutorId')
        student_id = self.request.get('studentId')
        gid = self.request.get('gid')

        if self.request.get('exit'):
            """ The session ended, update the session end"""
            autolog("Updating session end")
            session_list = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(ndb.AND(
                TutorHangoutSessions.tutor_id == tutor_id,
                TutorHangoutSessions.participant_id == student_id,
                TutorHangoutSessions.gid == gid,
                TutorHangoutSessions.duration <= 0.0)).fetch(1)

            if not session_list:
                autolog(
                    'TutorHangoutSession was not found: tutor_id {%s}, gid{%s}, student_id{%s}' % (
                        tutor_id, gid, student_id))
                self.response.set_status(204, "No session found for criteria.")
            else:
                session = session_list[0]
                now = datetime.datetime.now()
                delta = now - session.start
                session.end = now
                session.duration = delta.total_seconds() / 60  # convert to minutes
                session_key = session.put()
                self.response.out.write(session_key.urlsafe())

                tutor = TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).filter(
                    TutorSubjects.tutor_id == tutor_id).fetch(1)
                # Add tutor back to queue
                if tutor:
                    tutorQueue.appendleft(tutor[0])

        else:  # Create new TutorHangoutSession
            autolog("Creating new session")
            # Get subject from TutorSubjects, cause the client does not have it
            tutor = get_tutor_subjects(None, gid)
            if tutor:
                session = TutorHangoutSessions(parent=hapi.TUTOR_SESSIONS_PARENT_KEY,
                                               subject=tutor[0].subjects[0],
                                               tutor_id=self.request.get('tutorId'),
                                               tutor_name=self.request.get('tutorName'),
                                               gid=gid,
                                               duration=None,
                                               participant_id=self.request.get('studentId'),
                                               participant_name=self.request.get('studentName')
                )
                session_key = session.put()
                remove_tutor_from_queue(tutor[0].tutor_id)
                self.response.out.write(session_key.urlsafe())
            else:
                autolog('No TutorSubjects; can not create a Hangout Session row.')


class SubjectsHandler(BaseHandler):
    def get(self):
        """ Returns the list of subjects with available tutors """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        # remove_stale_sessions()
        update_subjects()

        try:
            subjects = HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).order(HangoutSubjects.subject).fetch()

            if subjects:
                return self.response.out.write(JSONEncoder().encode(subjects))
            else:
                self.response.set_status(204, 'No subjects found')
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

        return self.response.out.write(dump_json(surveys))


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
            tutor_subjects = get_tutor_subjects(None, gid)
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
