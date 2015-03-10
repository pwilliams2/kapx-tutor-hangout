from google.appengine.ext import ndb

import tutor_hangouts_api as hapi
from lib.base import BaseHandler
from models.models import TutorSubjects, TutorHangoutSessions, HangoutSubjects, TutorArchive
from utils import autolog


class DataHandler(BaseHandler):
    """ Data operations """

    @staticmethod
    def get_tutor_active_session(tutor_id=None, student_id=None, gid=None):
        """
        :param tutor_id:
        :param student_id:
        :param gid:
        :return:
        """
        if tutor_id and student_id and gid:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(ndb.AND(
                TutorHangoutSessions.tutor_id == tutor_id,
                TutorHangoutSessions.participant_id == student_id,
                TutorHangoutSessions.gid == gid,
                TutorHangoutSessions.duration <= 0.0)).fetch(1)
        elif tutor_id and student_id:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(ndb.AND(
                TutorHangoutSessions.tutor_id == tutor_id,
                TutorHangoutSessions.participant_id == student_id,
                TutorHangoutSessions.duration <= 0.0)).fetch(1)
        elif tutor_id and gid:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(ndb.AND(
                TutorHangoutSessions.tutor_id == tutor_id,
                TutorHangoutSessions.gid == gid,
                TutorHangoutSessions.duration <= 0.0)).fetch(1)
        elif tutor_id:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(ndb.AND(
                TutorHangoutSessions.tutor_id == tutor_id,
                TutorHangoutSessions.duration <= 0.0)).fetch(1)
        else:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(
                TutorHangoutSessions.duration <= 0.0).fetch(1)



    @staticmethod
    def get_tutor_sessions(tutor_id=None):
        """ Return the tutor sessions
        :param tutor_id:
        :return:
        """

        if tutor_id:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).filter(
                TutorHangoutSessions.tutor_id == tutor_id).fetch()
        else:
            return TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).fetch()

    @staticmethod
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
            return TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).order(
                -TutorSubjects.last_modified).fetch()


    @staticmethod
    def get_hangout_subjects(subject=None):
        """
        :param subject:
        :return:
        """

        if subject:
            return HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).filter(
                HangoutSubjects.subject == subject).fetch(1)
        else:
            return HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).order(HangoutSubjects.subject).fetch()

    @staticmethod
    def get_tutor_archive(tutor_id=None):
        """
        :param tutor_id:
        :return:
        """
        if tutor_id:
            return TutorArchive.query(ancestor=hapi.TUTOR_ARCHIVE_PARENT_KEY).filter(
                TutorArchive.tutor_id == tutor_id)
        else:
            return TutorArchive.query(ancestor=hapi.TUTOR_ARCHIVE_PARENT_KEY).order(-TutorArchive.last_modified).fetch(
                100)

    @staticmethod
    def aggregate_session_data(session_list):
        pass


    @staticmethod
    def update_tutor_archive(tutor_list):
        """ Compute elapsed time online and actual time in session
        :return:
        """
        autolog('updating TutorArchive...')
        elapsed = 0.0
        actual = 0.0
        for tutor in tutor_list:
            tutor_session_list = DataHandler.get_tutor_sessions(tutor.tutor_id)
            if tutor_session_list:
                DataHandler.aggregate_session_data(tutor_session_list)

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