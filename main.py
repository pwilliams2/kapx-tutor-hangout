#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#from google.appengine.ext.webapp import util
from google.appengine.ext import ndb

import webapp2


class MainHandler(webapp2.RequestHandler):
    def get(self):
        # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        # Print some JSON
        self.response.out.write('{"mainHandler":"Submit Clicked!"}\n')

class ReservationHandler(webapp2.RequestHandler):
    def get(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.

         # Set the cross origin resource sharing header to allow AJAX
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        # Print some JSON
        self.response.out.write(self.request.get('subjects'))
        self.response.out.write('{"message":"Submit Clicked!"}\n')


application = webapp2.WSGIApplication([
        ('/', MainHandler),
        ('/subjects', ReservationHandler)
    ], debug=True)

