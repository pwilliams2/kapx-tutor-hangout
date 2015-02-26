import base64
import inspect
import logging
import json
import time
from datetime import datetime, date
import urllib

from google.appengine.api import logservice
from google.appengine.ext import ndb
import webapp2


def autolog(message, level=None):
    "Automatically log the current function details."
    # Get the previous frame in the stack, otherwise it would
    # be this function!!!
    func = inspect.currentframe().f_back.f_code
    # Dump the message + the name of this function to the log.

    if level and level.lower() == 'info':
        logging.info("%s: %s in %s:%i" % (
            message,
            func.co_name,
            func.co_filename,
            func.co_firstlineno
        ))
    elif level and level.lower() == 'error':
        logging.error("%s: %s in %s:%i" % (
            message,
            func.co_name,
            func.co_filename,
            func.co_firstlineno
        ))
    else:
        logging.debug("%s: %s in %s:%i" % (
            message,
            func.co_name,
            func.co_filename,
            func.co_firstlineno
        ))


def dump_json(a_list):
    if a_list:
        data = {
            "data": [item for item in a_list]
        }
        return JSONEncoder().encode(data)
        # return json.dumps(data)
    else:
        return [{}]


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        # If this is a key, you might want to grab the actual model.
        if isinstance(o, ndb.Key):
            o = ndb.get(o)

        if isinstance(o, ndb.Model):
            return o.to_dict()
            # return db.to_dict(o)
        elif isinstance(o, (datetime, date, time)):
            return str(o)  # Or whatever other date format you're OK with...


class LogPage(webapp2.RequestHandler):
    def get(self):
        logging.info('Starting Main handler')
        # Get the incoming offset param from the Next link to advance through
        # the logs. (The first time the page is loaded, there won't be any offset.)
        try:
            offset = self.request.get('offset') or None
            if offset:
                offset = base64.urlsafe_b64decode(str(offset))
        except TypeError:
            offset = None

        # Set up end time for our query.
        end_time = time.time()

        # Count specifies the max number of RequestLogs shown at one time.
        # Use a boolean to initially turn off visiblity of the "Next" link.
        count = 5
        show_next = False
        last_offset = None

        # Iterate through all the RequestLog objects, displaying some fields and
        # iterate through all AppLogs beloging to each RequestLog count times.
        # In each iteration, save the offset to last_offset; the last one when
        # count is reached will be used for the link.
        i = 0
        for req_log in logservice.fetch(end_time=end_time, offset=offset,
                                        minimum_log_level=logservice.LOG_LEVEL_INFO,
                                        include_app_logs=True):
            self.response.out.write('<br /> REQUEST LOG <br />')
            self.response.out.write(
                'IP: %s <br /> Method: %s <br /> Resource: %s <br />' %
                (req_log.ip, req_log.method, req_log.resource))
            self.response.out.write(
                'Date: %s<br />' %
                datetime.fromtimestamp(req_log.end_time).strftime('%D %T UTC'))

            last_offset = req_log.offset
            i += 1

            for app_log in req_log.app_logs:
                self.response.out.write('<br />APP LOG<br />')
                self.response.out.write(
                    'Date: %s<br />' %
                    datetime.fromtimestamp(app_log.time).strftime('%D %T UTC'))
                self.response.out.write('<br />Message: %s<br />' % app_log.message)

            if i >= count:
                show_next = True
                break

        # Prepare the offset URL parameters, if any.
        if show_next:
            query = self.request.GET
            query['offset'] = base64.urlsafe_b64encode(last_offset)
            next_link = urllib.urlencode(query)
            self.response.out.write('<a href="/logs?%s">Next</a>' % next_link)


class PingHandler(webapp2.RequestHandler):
    def get(self):
        autolog("Pinghandler")


