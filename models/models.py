__author__ = 'pwilliams'

from google.appengine.ext import ndb

from endpoints_proto_datastore.ndb import EndpointsModel


class TutorSubjects(EndpointsModel):
    _message_fields_schema = \
        ('entityKey', 'tutor_id', 'subjects', 'tutor_name', 'create_date', 'last_modified', 'gid', 'max_participants',
         'participants_count')
    tutor_id = ndb.StringProperty()  # participant.person.id
    subjects = ndb.StringProperty(repeated=True)
    tutor_name = ndb.StringProperty()
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()
    max_participants = ndb.IntegerProperty()
    participants_count = ndb.IntegerProperty()

class TutorHangoutSessions(EndpointsModel):
    _message_fields_schema = (
        'entityKey', 'tutor_id', 'subject', 'gid', 'tutor_name', 'participant_id', 'participant_name', 'start', 'end',
        'duration', 'survey_key')
    tutor_id = ndb.StringProperty()  # participant.person.id
    subject = ndb.StringProperty()
    gid = ndb.StringProperty()
    tutor_name = ndb.StringProperty()
    participant_id = ndb.StringProperty()
    participant_name = ndb.StringProperty()
    start = ndb.DateTimeProperty(auto_now_add=True)
    end = ndb.DateTimeProperty()
    duration = ndb.FloatProperty()
    survey_key = ndb.StringProperty()


class HangoutSubjects(EndpointsModel):
    _message_fields_schema = ('entityKey', 'subject', 'is_available', 'last_modified', 'gid', 'image_url')
    subject = ndb.StringProperty()
    is_available = ndb.BooleanProperty()
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()
    image_url = ndb.StringProperty(indexed=False)

class TutorSurveys(EndpointsModel):
    _message_fields_schema = ('entityKey', 'subject', 'student_id','tutor_id','tutor_name', 'create_date', 'last_modified', 'knowledge',
                              'communications','overall','comments')
    subject = ndb.StringProperty()
    student_id = ndb.StringProperty()
    tutor_id = ndb.StringProperty()
    tutor_name = ndb.StringProperty()
    student_name = ndb.StringProperty()
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    knowledge = ndb.FloatProperty()
    communications = ndb.FloatProperty()
    overall = ndb.FloatProperty()
    gid = ndb.StringProperty()
    comments = ndb.StringProperty()
