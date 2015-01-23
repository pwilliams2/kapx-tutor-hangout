__author__ = 'pwilliams'

import endpoints
import protorpc

from models.models import HangoutSubjects,TutorSubjects, TutorHangoutSessions
import main

API_ROOT = 'https://kx-tutor-hangout-app.appspot.com/_ah/api'
API = 'tutorhangouts'
VERSION = 'v1'

@endpoints.api(name="tutorhangouts", version="v1", description="Tutor Hangout API")
class TutorHangoutsApi(protorpc.remote.Service):
    """ API for the CRUD methods """

    @HangoutSubjects.query_method (query_fields=("limit", "order","pageToken"), name="subjects.list", path="/subjects", http_method="GET")
    def hangoutsubjects_list(self, query):
         """ get all the Hangout Subjects """
         return query

    @HangoutSubjects.method(name="subjects.insert", path="/subjects", http_method="POST")
    def hangoutsubjects_insert(self, request):
        """ insert or update """
        if request.from_datastore:
            mq = request
        else:
            mq = HangoutSubjects(parent=main.PARENT_KEY, quote=request.quote, movie=request.movie)

        mq.put()
        return mq

    @HangoutSubjects.method(request_fields=("entityKey",),name="subjects.delete", path="/subjects/{entityKey}", http_method="DELETE")
    def hangoutsubjects_delete(self, request):
        """ Delete HangoutSubjects, if exists """
        if not request.from_datastore:
            raise endpoints.NotFoundException("Hangout subject to be deleted was not found")

        request.key.delete()
        return HangoutSubjects(quote="delete")



app = endpoints.api_server([TutorHangoutsApi], restricted=False)



