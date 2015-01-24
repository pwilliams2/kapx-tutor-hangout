__author__ = 'pwilliams'

import endpoints

import protorpc

from models.models import HangoutSubjects, TutorSubjects, TutorHangoutSessions
import main


API_ROOT = 'https://kx-tutor-hangout-app.appspot.com/_ah/api'
API_NAME = 'tutorhangouts'
VERSION = 'v1'


@endpoints.api(name=API_NAME, version=VERSION, description="Tutor Hangout API")
class TutorHangoutsApi(protorpc.remote.Service):
    """ API for the CRUD methods """

    @HangoutSubjects.query_method(query_fields=("limit", "order", "pageToken"), name="subjects.list", path="/subjects",
                                  http_method="GET")
    def hangoutsubjects_list(self, query):
        """ Get the Hangout Subjects and their availability """
        return query


    @HangoutSubjects.method(name="subjects.insert", path="/subjects", http_method="POST")
    def hangoutsubjects_insert(self, request):
        """ Insert / Update a Hangout Subject """
        if request.from_datastore:
            hangout_subject = request
        else:
            hangout_subject = HangoutSubjects(parent=main.SUBJECTS_PARENT_KEY,
                                              subject=request.subject,
                                              isAvailable=request.state)

        hangout_subject.put()
        return hangout_subject

    @HangoutSubjects.method(request_fields=("entityKey",), name="subjects.delete", path="/subjects/{entityKey}",
                            http_method="DELETE")
    def hangoutsubjects_delete(self, request):
        """ Delete a Hangout Subject, if exists """
        if not request.from_datastore:
            raise endpoints.NotFoundException("Hangout subject to be deleted was not found")

        request.key.delete()
        return HangoutSubjects(quote="delete")

    # @TutorSubjects.query_method(query_fields=("limit", "order", "pageToken"), name="tutor-subjects.list",
    #                             path="/tutor-subjects", http_method="GET")
    # def tutor_subjects_list(self, query):
    #     """ Get the Tutor Subjects """
    #     return query
    #
    # @TutorSubjects.method(name="tutor-subjects.insert", path="/tutor-subjects/{entityKey}", http_method="POST")
    # def tutor_subjects_insert(self, request):
    #     """ Insert / Update the Tutors and subjects """
    #     if request.from_datastore:
    #         tutor_subjects = request
    #     else:
    #         tutor_subjects = TutorSubjects(parent=main.TUTOR_SUBJECTS_PARENT_KEY,
    #                                        person_id=request.pid,
    #                                        subjects=request.subjects,
    #                                        tutor_name=request.pName,
    #                                        gid=request.gid)
    #     tutor_subjects.put()
    #     return tutor_subjects


app = endpoints.api_server([TutorHangoutsApi], restricted=False)



