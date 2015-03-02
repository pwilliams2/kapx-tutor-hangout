import json
import datetime
from collections import deque

from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine import runtime
from google.appengine.ext import ndb

import data
import tutor_hangouts_api as hapi
from utils import JSONEncoder, autolog, dump_json
from lib.base import BaseHandler
from models.models import TutorSubjects, TutorHangoutSessions


_tutorQueue = deque()  # FIFO q to serve subscribers
HANGOUTS_URL = 'https://talkgadget.google.com/hangouts/_/'


def remove_stale_sessions():
    """ When a tutor closes their H-O, remove them from the available subjects """
    autolog("remove_stale_sessions")
    now = datetime.datetime.now()
    tutor_list = data.DataHandler.get_tutor_subjects()

    if tutor_list:
        del_list = [tutor for tutor in tutor_list
                    if (now - tutor.last_modified).total_seconds() > 120]  # Tutor heartbeat older than 60s
        if del_list:
            autolog('last_modified age: {0}'.format((now - del_list[0].last_modified).total_seconds()))
            del_keys = [tutor.key for tutor in del_list]
            ndb.delete_multi(del_keys)
            data.DataHandler.update_tutor_archive(del_list)  # Add it to the archive


def assign_available_tutors(subjects_list):
    """ Assign the tutors in the avail_tutors_list to the subjects in the subjects_list
    :param subjects_list: the tutored subjects
    :return:
    """

    try:
        autolog('_tutorQueue size %s' % str(len(_tutorQueue)))

        size = len(_tutorQueue)
        for subject in subjects_list:  # Get next an available tutor in q
            i = 0
            subject.is_available = False
            subject.gid = ''

            while _tutorQueue and i < size:
                i += 1
                current_tutor = _tutorQueue.pop()

                tutor_list = data.DataHandler.get_tutor_subjects(current_tutor.tutor_id, current_tutor.gid)

                if tutor_list:
                    tutor = tutor_list[0]
                    if subject.subject in tutor.subjects and tutor.participants_count < tutor.max_participants:
                        autolog('Tutor match found for: {0}'.format(subject.subject))
                        subject.gid = tutor.gid  # Assign a tutor to the subject
                        subject.is_available = True
                        subject.put()
                        _tutorQueue.appendleft(tutor)  # Put the tutor back in the q
                        break
                    else:
                        _tutorQueue.appendleft(tutor)  # Put the tutor back in the q
            subject.put()
        return True
    except OverQuotaError, e:
        autolog('Over Quota Error, bypassing for now: %s ' % str(e))
        raise


def remove_tutor_from_queue(tutor_id):
    """  When a tutor starts a session with a client (student), remove them from avail queue
    :param tutor_id:
    :return:
    """

    size = len(_tutorQueue)
    i = 0
    while i < size:
        i += 1
        tutor = _tutorQueue.pop()
        if tutor.tutor_id == tutor_id:
            return True
        else:
            _tutorQueue.appendleft(tutor)  # Put it back if it doesn't match
    return False


def update_subjects():
    """ Update the subjects table to reflect the availability of the current tutors """
    subjects_list = data.DataHandler.get_hangout_subjects()

    # Retrieve Available Tutors and their subjects
    if data.DataHandler.get_tutor_subjects():  # There are tutors available
        autolog('There are avail_tutors.')
        assign_available_tutors(subjects_list)
    else:
        autolog('No available tutors.')
        avail_list = [item for item in subjects_list if item.is_available]
        for subject in avail_list:  # Set all subjects to unavailable
            autolog('setting subject %s to false' % subject.subject)
            try:
                subject.is_available = False
                subject.gid = None
                subject.put()
            except OverQuotaError, e:
                autolog('Over Quota Error, bypassing for now: ' + str(e))


class HangoutRequestHandler(BaseHandler):
    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        gid = self.get_required_value(self.request.get('gid'))
        subject = self.request.get('subject')
        autolog("HangoutRequestHandler url {0}{gid}?gd={subject}".format(HANGOUTS_URL, gid=gid, subject=subject))

        return self.redirect('{0}{gid}?gd={subject}'.format(HANGOUTS_URL, gid=gid, subject=subject))


class HeartbeatHandler(BaseHandler):
    """ Heartbeat of the tutor's hangout  """

    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.response.headers['Content-Type'] = 'text/plain'

        # Search for the specified tutor id == pid
        tutor_subjects = data.DataHandler.get_tutor_subjects(self.get_required_value(self.request.get('gid'), 'gid'))

        try:
            count = int(self.request.get("count"))
        except ValueError, e:
            autolog("Invalid count: %s" % str(e))
            count = 1

        if tutor_subjects:
            tutor_subject = tutor_subjects[0]
            tutor_subject.gid = self.request.get('gid')
            tutor_subject.participants_count = count
            tutor_subject.put()

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
            tutor_subjects = data.DataHandler.get_tutor_subjects(self.get_required_value(self.request.get('pid'), 'pid'),
                                                                 self.get_required_value(self.request.get('gid'), 'gid'))

            count = int(self.request.get('count')) if self.request.get('count') else 0
            max_participants = int(self.request.get('maxParticipants')) if self.request.get('maxParticipants') else 1
            inp_subjects = self.get_required_value(self.request.get('subjects'), 'subjects')

            avail_subjects = []
            if isinstance(self.request.get('subjects'), basestring):
                avail_subjects = [str(tutor_subject['subject']) for tutor_subject in json.loads(inp_subjects)]

            if tutor_subjects:
                tutor = tutor_subjects[0]
                autolog("Updating tutor subject")
                tutor.gid = self.request.get('gid')
                tutor.subjects = avail_subjects
                tutor.participants_count = count
                tutor.max_participants = max_participants
                ts_key = tutor.put()

                autolog("Tutor subjects: %s" % str(tutor.subjects))
                if len(_tutorQueue) == 0:
                    _tutorQueue.appendleft(tutor)
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
                _tutorQueue.appendleft(tutor)
            self.response.out.write(ts_key.urlsafe())
        except Exception, e:
            autolog('msg: ' + str(e))


class SessionHandler(BaseHandler):
    def get(self):
        """ List of sessions      """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        ths_list = data.DataHandler.get_tutor_sessions()
        return self.response.out.write(dump_json(ths_list))


class SubscribeHandler(BaseHandler):
    """ Update the TutorHangoutSessions store  """

    def get(self):
        """ Get the list of TutorHangoutSessions """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        ths_list = data.DataHandler.get_tutor_sessions()
        return self.response.out.write(dump_json(ths_list))

    def post(self):
        """ Subscribe client for H-O session"""
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        autolog("updating tutor hangout session")

        tutor_id = self.get_required_value(self.request.get('tutorId'), 'tutorId')
        student_id = self.get_required_value(self.request.get('studentId'), 'student_id')
        gid = self.get_required_value(self.request.get('gid'), 'gid')

        if self.request.get('exit'):
            """ The session ended, update the session end"""
            autolog("Updating session end")
            session_list = data.DataHandler.get_student_active_session(tutor_id, student_id, gid)

            if session_list:
                session = session_list[0]
                now = datetime.datetime.now()
                delta = now - session.start
                session.end = now
                session.duration = delta.total_seconds() / 60  # convert to minutes
                session_key = session.put()
                self.response.out.write(session_key.urlsafe())

                tutor = data.DataHandler.get_tutor_subjects(tutor_id)
                # Add tutor back to queue
                if tutor:
                    _tutorQueue.appendleft(tutor[0])
            else:
                autolog(
                    'TutorHangoutSession was not found: tutor_id {%s}, gid{%s}, student_id{%s}' % (
                        tutor_id, gid, student_id))
                self.response.set_status(204, "No session found for criteria.")

        else:  # Create new TutorHangoutSession
            autolog("Creating new session")
            # Get subject from TutorSubjects cause the client does not have it
            tutor = data.DataHandler.get_tutor_subjects(tutor_id, gid)
            if tutor:
                session = TutorHangoutSessions(parent=hapi.TUTOR_SESSIONS_PARENT_KEY,
                                               subject=tutor[0].subjects[0],
                                               tutor_id=tutor_id,
                                               tutor_name=self.request.get('tutorName'),
                                               gid=gid,
                                               duration=None,
                                               participant_id=student_id,
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
        remove_stale_sessions()
        update_subjects()

        try:
            subjects = data.DataHandler.get_hangout_subjects()

            if subjects:
                return self.response.out.write(JSONEncoder().encode(subjects))
            else:
                self.response.set_status(204, 'No subjects found')
                autolog("no subjects found")
                return None
        except runtime.DeadlineExceededError, e:
            autolog('Deadline Exceed Error: ' + str(e))
            return None