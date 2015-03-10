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
    """ Assign the tutors in the avail_tutors_list to the subjects in the subjects_list displayed to clients
    :param subjects_list: the tutored subjects
    :return:
    """

    try:
        autolog('_tutorQueue size %s' % str(len(_tutorQueue)))

        size = len(_tutorQueue)
        for subject in subjects_list:  # Get next available tutor in q
            i = 0
            subject.is_available = False
            subject.is_busy = False
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
        autolog('Over Quota Error, bypassing for now: %s ' % e.message)
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
    tutor_list = data.DataHandler.get_tutor_subjects()

    # Retrieve Available Tutors and their subjects
    if tutor_list:  # There are tutors available
        autolog('There are avail_tutors.')
        if subjects_list:
            assign_available_tutors(subjects_list)
            update_subject_busy_flag()

    else:
        autolog('No available tutors.')
        avail_list = [item for item in subjects_list if item.is_available]
        for subject in avail_list:  # Set all subjects to unavailable
            autolog('setting subject %s to false' % subject.subject)
            try:
                subject.is_available = False
                subject.is_busy = False
                subject.gid = None
                subject.put()
            except OverQuotaError, e:
                autolog('Over Quota Error, bypassing for now: ' + e.message)


def update_subject_busy_flag():
    """ There are two subject states:
     1) Not Available: There are no tutors online for that subject
     2) Busy: One or more tutors for a subject are online, but none are available, i.e., they're currently in a session
     Check if all available tutor(s) are in session for subject, if so, set the subject.is_busy to True
    :return:
    """

    try:
        subjects_list = data.DataHandler.get_hangout_subjects()
        tutor_subjects_list = data.DataHandler.get_tutor_subjects()
        for subject in subjects_list:
            tutor_list = [tutor_subject for tutor_subject in tutor_subjects_list if
                          subject.subject in tutor_subject.subjects]  # All tutors for subject

            if tutor_list:  # See if all tutors are already in a session
                active_session_list = [tutor_subject for tutor_subject in tutor_list
                                       if data.DataHandler.get_tutor_active_session(tutor_subject.tutor_id)]
                if len(active_session_list) == len(tutor_list):  # All tutors for subject are in session
                    subject.is_busy = True
                    subject.put()

    except Exception, e:
        autolog(e.message)


class HangoutRequestHandler(BaseHandler):
    """ Launch the student H-O """

    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        gid = self.get_required_value(self.request.get('gid'))
        subject = self.get_required_value(self.request.get('subject'))

        autolog("HangoutRequestHandler url {0}{gid}?gd={subject}".format(HANGOUTS_URL, gid=gid, subject=subject))
        return self.redirect('{0}{gid}?gd={subject}'.format(HANGOUTS_URL, gid=gid, subject=subject))


class HeartbeatHandler(BaseHandler):
    """ Heartbeat of the tutor's hangout  """

    def get(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")

        try:
            count = int(self.request.get("count"))
        except ValueError, e:
            autolog("Invalid count: %s" % str(e))
            count = 1

        try:
            tutor_subjects = data.DataHandler.get_tutor_subjects(
                self.get_required_value(self.request.get('pid')),
                self.get_required_value(self.request.get('gid'))
            )

            if tutor_subjects:
                tutor_subject = tutor_subjects[0]
                tutor_subject.gid = self.request.get('gid')
                tutor_subject.participants_count = count
                tutor_subject.put()
                autolog('last_modified {0}'.format(tutor_subject.last_modified))
                self.response.set_status(200, 'ok')

        except ValueError, e:
            autolog(e)
            self.response.set_status(500, e.message)

        remove_stale_sessions()  # cleanup closed sessions
        update_subjects()  # Update available subjects


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
            tutor_subjects = data.DataHandler.get_tutor_subjects(
                self.get_required_value(self.request.get('pid')),
                self.get_required_value(self.request.get('gid'))
            )

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
            autolog('msg: ' + e.message)


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

        try:
            if self.request.get('exit'):  # The session ended, update the session end
                self.exit_session()

            else:  # Create new TutorHangoutSession
                autolog("updating tutor hangout session")
                tutor_id = self.get_required_value(self.request.get('tutorId'), 'tutorId')
                student_id = self.get_required_value(self.request.get('studentId'), 'studentId')
                gid = self.get_required_value(self.request.get('gid'))

                autolog("Creating new session")
                # Get subject from TutorSubjects cause the client does not have it
                tutor_list = data.DataHandler.get_tutor_subjects(tutor_id, gid)

                if tutor_list:
                    session = TutorHangoutSessions(parent=hapi.TUTOR_SESSIONS_PARENT_KEY,
                                                   subject=tutor_list[0].subjects[0],
                                                   tutor_id=tutor_id,
                                                   tutor_name=self.request.get('tutorName'),
                                                   gid=gid,
                                                   duration=None,
                                                   participant_id=student_id,
                                                   participant_name=self.request.get('studentName')
                    )
                    session_key = session.put()
                    remove_tutor_from_queue(tutor_list[0].tutor_id)
                    self.response.out.write(session_key.urlsafe())

                else:
                    autolog('No TutorSubjects; can not create a Hangout Session row.')
        except ValueError, e:
            autolog(e.message)

    def exit_session(self):
        """
        :return:
        """
        autolog("Exiting the session...")
        tutor_id = self.get_required_value(self.request.get('tutorId'))
        student_id = self.get_required_value(self.request.get('studentId'))
        gid = self.get_required_value(self.request.get('gid'))

        session_list = data.DataHandler.get_tutor_active_session(tutor_id, student_id, gid)

        if session_list:
            session = session_list[0]
            now = datetime.datetime.now()
            delta = now - session.start
            session.end = now
            session.duration = delta.total_seconds() / 60  # convert to minutes
            session_key = session.put()
            self.response.out.write(session_key.urlsafe())

            tutor_list = data.DataHandler.get_tutor_subjects(tutor_id)
            # Add tutor back to queue
            if tutor_list:
                _tutorQueue.appendleft(tutor_list[0])
        else:
            autolog(
                'TutorHangoutSession was not found: tutor_id {%s}, gid{%s}, student_id{%s}' % (
                    tutor_id, gid, student_id))
            self.response.set_status(204, "No session found for criteria.")


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
                return []
        except runtime.DeadlineExceededError, e:
            autolog('Deadline Exceed Error: {0}'.format(e.message))
            return []

