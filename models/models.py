__author__ = 'pwilliams'


from endpoints_proto_datastore.ndb import EndpointsModel
from google.appengine.ext import ndb

class TutorSubjects(EndpointsModel):
    person_id = ndb.StringProperty() #participant.person.id
    subjects = ndb.StringProperty()
    tutor_name = ndb.StringProperty(indexed=False)
    create_date = ndb.DateTimeProperty(auto_now_add=True)

class TutorHangoutSessions(EndpointsModel):
    person_id = ndb.StringProperty()
    subjects = ndb.StringProperty()
    gid = ndb.StringProperty()
    tutor_name = ndb.StringProperty(indexed=False)
    start = ndb.DateTimeProperty(auto_now_add=True)
    end = ndb.DateTimeProperty()

class HangoutSubjects(EndpointsModel):
    subject = ndb.StringProperty()
    isAvailable = ndb.BooleanProperty(indexed=False)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()
    image_url = ndb.StringProperty()