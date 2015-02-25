from google.appengine.ext import ndb

import tutor_hangouts_api as hapi
from lib.base import BaseHandler
from models.models import TutorSubjects, TutorHangoutSessions, HangoutSubjects, TutorArchive


class DataHandler(BaseHandler):
    """ Data operations """

    @staticmethod
    def get_student_active_session(tutor_id=None, student_id=None, gid=None):
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
        else:
            raise ValueError("Requires tutor_id, student_id, and gid")

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
            return TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).fetch()


    @staticmethod
    def get_hangout_subjects():
        """
        :return:
        """
        return HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).order(HangoutSubjects.subject).fetch()