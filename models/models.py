__author__ = 'pwilliams'

from google.appengine.ext import ndb

from endpoints_proto_datastore.ndb import EndpointsModel


class TutorSubjects(EndpointsModel):
    _message_fields_schema = \
        ('entityKey', 'person_id', 'subjects', 'tutor_name', 'create_date', 'last_modified', 'gid', 'max_participants',
         'participants_count')
    person_id = ndb.StringProperty()  # participant.person.id
    subjects = ndb.StringProperty()
    tutor_name = ndb.StringProperty()
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()
    max_participants = ndb.IntegerProperty()
    participants_count = ndb.IntegerProperty()


class TutorHangoutSessions(EndpointsModel):
    _message_fields_schema = (
        'entityKey', 'tutor_id', 'subject', 'gid', 'tutor_name', 'participant_id', 'participant_name', 'start', 'end',
        'duration')
    tutor_id = ndb.StringProperty()  # participant.person.id
    subject = ndb.StringProperty()
    gid = ndb.StringProperty()
    tutor_name = ndb.StringProperty()
    participant_id = ndb.StringProperty()
    participant_name = ndb.StringProperty()
    start = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    end = ndb.DateTimeProperty(indexed=False)
    duration = ndb.FloatProperty()


class HangoutSubjects(EndpointsModel):
    _message_fields_schema = ('entityKey', 'subject', 'is_available', 'last_modified', 'gid', 'image_url')
    subject = ndb.StringProperty()
    is_available = ndb.BooleanProperty(indexed=False)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()
    image_url = ndb.StringProperty(indexed=False)