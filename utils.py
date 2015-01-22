
import json
from datetime import datetime, date, time
from google.appengine.ext import ndb


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        # If this is a key, you might want to grab the actual model.
        if isinstance(o, ndb.Key):
            o = ndb.get(o)

        if isinstance(o, ndb.Model):
            return o.to_dict()
            #return db.to_dict(o)
        elif isinstance(o, (datetime, date, time)):
            return str(o)  # Or whatever other date format you're OK with...
