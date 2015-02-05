import logging

from google.appengine.ext import ndb


__author__ = 'pwilliams'

import endpoints

import protorpc

from models.models import HangoutSubjects, TutorSubjects, TutorHangoutSessions

# API_ROOT = 'http://localhost:8080/_ah/api'
API_ROOT = 'https://kx-tutor-hangout-app.appspot.com/_ah/api'
API_NAME = 'tutorhangouts'
VERSION = 'v1'

SUBJECTS_PARENT_KEY = ndb.Key("Entity", 'subjects_root')
TUTOR_SUBJECTS_PARENT_KEY = ndb.Key("Entity", 'tutor_subjects_root')
TUTOR_SESSIONS_PARENT_KEY = ndb.Key("Entity", 'tutor_sessions_root')


@endpoints.api(name=API_NAME, version=VERSION, description="Tutor Hangout API")
class TutorHangoutsApi(protorpc.remote.Service):
    """ API for the CRUD methods """

    @HangoutSubjects.query_method(query_fields=("limit", "order", "pageToken"), name="subjects.list", path="/subjects",
                                  http_method="GET")
    def hangoutsubjects_list(self, query):
        """ Get the Hangout Subjects and their availability """
        return query


    @HangoutSubjects.method(name="subjects.insert", path="/subjects", http_method="POST")
    def hangout_subjects_insert(self, request):
        """ Insert / Update a Hangout Subject """
        logging.info("Hangout Subjects Insert")
        hangout_subject = HangoutSubjects(parent=SUBJECTS_PARENT_KEY,
                                          subject=request.subject,
                                          is_available=request.is_available,
                                          gid=request.gid)

        hangout_subject.put()
        return hangout_subject

    @HangoutSubjects.method(name="subjects.update", path="/subjects/{entityKey}", http_method="POST")
    def hangout_subjects_update(self, request):
        """ Update a Hangout Subject """

        if not request.from_datastore:
            raise endpoints.NotFoundException('Tutor Subject for update not found.')

        logging.info('Hangout Subjects update, entity_key %s' % request.entityKey)
        hangout_subject = request

        hangout_subject.put()
        return hangout_subject

    @HangoutSubjects.method(request_fields=("id",), name="subjects.delete", path="/subjects/{id}",
                            http_method="DELETE")
    def hangout_subjects_delete(self, request):
        """ Delete a Hangout Subject, if exists """
        if not request.from_datastore:
            raise endpoints.NotFoundException("Hangout subject to be deleted was not found")

        request.key.delete()


    @TutorSubjects.query_method(query_fields=("entityKey", "limit", "order", "pageToken"),
                                name="tutor_subjects.list",
                                path="/tutorsubjects", http_method="GET")
    def tutor_subjects_list(self, query):
        """ Get the Tutor Subjects """
        return query

    @TutorSubjects.method(name="tutor_subjects.insert", path="/tutorsubjects", http_method="POST")
    def tutor_subjects_insert(self, request):
        """ Insert the Tutor subjects """

        logging.info("endpoint tutor subjects insert")
        tutor_subjects = TutorSubjects(parent=TUTOR_SUBJECTS_PARENT_KEY,
                                       person_id=request.person_id,
                                       subjects=request.subjects,
                                       tutor_name=request.tutor_name,
                                       gid=request.gid,
                                       max_participants=request.max_participants,
                                       participants_count=request.participants_count)

        tutor_subjects.put()
        return tutor_subjects


    @TutorSubjects.method(name="tutor_subjects.update", path="/tutorsubjects/{entityKey}",
                          http_method="POST")
    def tutor_subjects_update(self, request):
        """  Update the Tutor subjects """

        logging.info("endpoint tutor subjects update")
        if not request.from_datastore:
            raise endpoints.NotFoundException('Tutor Subject for update not found.')

        logging.info('entity_keys %s' % request.entityKey)
        ts = request
        ts.put()
        return ts

    @TutorSubjects.method(request_fields=("entityKey",), name="tutor_subjects.delete",
                          path="/tutorsubjects/{entityKey}",
                          http_method="DELETE")
    def tutor_subjects_delete(self, request):
        """ Delete a Hangout Subject, if exists """
        if not request.from_datastore:
            raise endpoints.NotFoundException("Tutor subject to be deleted was not found.")

        request.key.delete()
        return TutorSubjects(gid="deleted")


    @TutorHangoutSessions.query_method(query_fields=("entityKey", "limit", "order", "pageToken"),
                                name="tutor_sessions.list",
                                path="/tutorsessions", http_method="GET")
    def tutor_hangout_sessions_list(self, query):
        """ Get the Tutor Sessions """
        return query
    @TutorHangoutSessions.method(name="tutor_sessions.insert", path="/tutorsessions", http_method="POST")
    def tutor_hangout_sessions_insert(self, request):
        """ Insert the Tutor Hangout Session """

        logging.info("EP Tutor Subjects insert")
        tutor_sessions = TutorHangoutSessions(parent=TUTOR_SESSIONS_PARENT_KEY,
                                              person_id=request.person_id,
                                              subject=request.subject,
                                              tutor_name=request.tutor_name,
                                              gid=request.gid)

        tutor_sessions.put()
        return tutor_sessions


    @TutorHangoutSessions.method(name="tutor_sessions.update", path="/tutorsessions/{entityKey}",
                                 http_method="POST")
    def tutor_hangout_sessions_update(self, request):
        """  Update the Tutor Hangout Session """

        logging.info("EP Tutor Hangout Sessions update")
        if not request.from_datastore:
            raise endpoints.NotFoundException('Tutor Hangout Session for update not found.')

        logging.info('entity_keys %s' % request.entityKey)
        ts = request
        ts.put()
        return ts


app = endpoints.api_server([TutorHangoutsApi], restricted=False)



