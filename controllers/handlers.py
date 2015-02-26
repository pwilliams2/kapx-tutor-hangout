import json
import datetime
from collections import deque

from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine import runtime
from google.appengine.ext import ndb

from data import DataHandler

import tutor_hangouts_api as hapi
from utils import JSONEncoder, autolog, dump_json
from lib.base import BaseHandler
from models.models import TutorSubjects, TutorHangoutSessions, TutorArchive


_tutorQueue = deque()  # FIFO q to serve subscribers
_is_subjects_available = True


def remove_stale_sessions():
    """ When a tutor closes their H-O, we need to remove them from the available subjects """
    autolog("remove_stale_sessions")
    now = datetime.datetime.now()
    del_list = DataHandler.get_tutor_subjects()

    if del_list and del_list:
        autolog('del_list')
        keys = []
        for tutor in del_list:
            delta = now - tutor.last_modified
            if delta.total_seconds() > 60:
                keys.append(tutor.key)
                update_tutor_archive(tutor)

        if keys:
            autolog('deleting tutor keys ' % keys)
            ndb.delete_multi(keys)


def update_tutor_archive(tutor):
    """ Compute elapsed time online and actual time in session
    :return:
    """
    autolog('updating TutorArchive...')
    elapsed = 0.0
    actual = 0.0
    tutor_session_list = DataHandler.get_tutor_sessions(tutor.tutor_id)
    if tutor_session_list:
        aggregate_session_data(tutor_session_list)

    tutor_archive = DataHandler.get_tutor_archive(tutor.tutor_id)
    if tutor_archive:
        pass
    else:
        tutor_archive = TutorArchive(parent=hapi.TUTOR_ARCHIVE_PARENT_KEY,
                                     tutor_id=tutor.tutor_id,
                                     tutor_name=tutor.tutor_name,
                                     subjects=tutor.subjects,
                                     elapsed_time=elapsed,
                                     actual_time=actual
        )
        tutor_archive.put()


def aggregate_session_data(session_list):
    pass


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

                tutor_list = DataHandler.get_tutor_subjects(current_tutor.tutor_id, current_tutor.gid)
                if tutor_list:
                    tutor = tutor_list[0]

                    if subject.subject in tutor.subjects and tutor.participants_count < tutor.max_participants:
                        autolog('Tutor match found for: %s' % subject.subject)
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


def update_subjects():
    """ Update the subjects table to reflect the availability of the current tutors """
    subjects_list = DataHandler.get_hangout_subjects()

    # Retrieve Available Tutors and their subjects
    if not DataHandler.get_tutor_subjects():  # There are no tutors available
        autolog('No available tutors.')
        assigned_list = [item for item in subjects_list if item.is_available]
        for subject in assigned_list:  # Set all subjects to unavailable
            autolog('setting subject %s to false' % subject.subject)
            try:
                subject.is_available = False
                subject.gid = None
                subject.put()
            except OverQuotaError, e:
                autolog('Over Quota Error, bypassing for now: ' + str(e))
    else:
        autolog('There are avail_tutors.')
        assign_available_tutors(subjects_list)


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
        ts_list = DataHandler.get_tutor_subjects(self.request.get('pid'))

        count = 1
        if not ts_list:  # hangout is no longer available
            pass
        else:  # Found an existing tutor tutor_id, then update the count
            if self.request.get("count") and isinstance(self.request.get("count"), int):
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
            tutor = DataHandler.get_tutor_subjects(self.request.get('pid'), self.request.get('gid'))

            count = int(self.request.get('count')) if self.request.get('count') else 0
            max_participants = int(self.request.get('maxParticipants')) if self.request.get('maxParticipants') else 1
            inp_subjects = self.request.get('subjects') if self.request.get('subjects') else ''

            avail_subjects = []
            if inp_subjects and isinstance(self.request.get('subjects'), basestring):
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

        ths_list = DataHandler.get_tutor_sessions()
        return self.response.out.write(dump_json(ths_list))


class SubscribeHandler(BaseHandler):
    """ Update the TutorHangoutSessions store  """

    def get(self):
        """ Get the list of TutorHangoutSessions """
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        ths_list = DataHandler.get_tutor_sessions()
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
            session_list = DataHandler.get_student_active_session(tutor_id, student_id, gid)

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

                tutor = DataHandler.get_tutor_subjects(tutor_id)
                # Add tutor back to queue
                if tutor:
                    _tutorQueue.appendleft(tutor[0])

        else:  # Create new TutorHangoutSession
            autolog("Creating new session")
            # Get subject from TutorSubjects, cause the client does not have it
            tutor = DataHandler.get_tutor_subjects(None, gid)
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
        remove_stale_sessions()
        update_subjects()

        try:
            subjects = DataHandler.get_hangout_subjects()

            if subjects:
                return self.response.out.write(JSONEncoder().encode(subjects))
            else:
                self.response.set_status(204, 'No subjects found')
                autolog("no subjects found")
                return None
        except runtime.DeadlineExceededError, e:
            autolog('Deadline Exceed Error: ' + str(e))
            return None