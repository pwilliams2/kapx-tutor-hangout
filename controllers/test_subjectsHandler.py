
from webtest import TestApp
from unittest import TestCase
import sys
import os
import main
import config

from google.appengine.runtime import apiproxy_errors
from google.appengine.ext import ndb

__author__ = 'admin'
sys.path.insert(1, os.path.join(os.path.abspath('.'), 'lib'))

import handlers

class TestSubjectsHandler(TestCase):
    def test_get(self):
        self.sh = handlers.SubjectsHandler(self)
        self.assertTrue(self.sh.get(self), msg="No subjects")