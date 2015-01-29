__author__ = 'pwilliams'

from google.appengine.ext import ndb

from endpoints_proto_datastore.ndb import EndpointsModel


class TutorSubjects(EndpointsModel):
    _message_fields_schema = ('entityKey','person_id','subjects','tutor_name','create_date', 'last_modified', 'gid')
    person_id = ndb.StringProperty() #participant.person.id
    subjects = ndb.StringProperty()
    tutor_name = ndb.StringProperty()
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()

class TutorHangoutSessions(EndpointsModel):
    _message_fields_schema = ('entityKey','person_id','subjects','gid','tutor_name','start', 'end')
    person_id = ndb.StringProperty()
    subjects = ndb.StringProperty()
    gid = ndb.StringProperty()
    tutor_name = ndb.StringProperty(indexed=False)
    start = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    end = ndb.DateTimeProperty(indexed=False)

class HangoutSubjects(EndpointsModel):
    _message_fields_schema = ('entityKey','subject','is_available','last_modified','gid', 'image_url')
    subject = ndb.StringProperty()
    is_available = ndb.BooleanProperty(indexed=False)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()
    image_url = ndb.StringProperty(indexed=False)