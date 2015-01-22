__author__ = 'admin'

from google.appengine.ext import ndb

class TutorSubjects(ndb.Model):
    id = ndb.StringProperty()
    subjects = ndb.StringProperty()
    tutor_name = ndb.StringProperty(indexed=False)
    create_date = ndb.DateTimeProperty(auto_now_add=True)


class TutorHangoutSessions(ndb.Model):
    id = ndb.StringProperty()
    subjects = ndb.StringProperty()
    gid = ndb.StringProperty()
    tutor_name = ndb.StringProperty(indexed=False)
    start = ndb.DateTimeProperty(auto_now_add=True)
    end = ndb.DateTimeProperty()

class HangoutSubjects(ndb.Model):
    subject = ndb.StringProperty()
    isAvailable = ndb.BooleanProperty(indexed=False)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    gid = ndb.StringProperty()