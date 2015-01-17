__author__ = 'admin'

from google.appengine.ext import ndb

class Tutor(ndb.Model):
    id = ndb.StringProperty()
    subjects = ndb.StringProperty()
    gid = ndb.StringProperty()
    name = ndb.StringProperty(indexed=False)
    create_date = ndb.DateTimeProperty(auto_now_add=True)
