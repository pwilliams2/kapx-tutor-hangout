import sys
import os
import config


# sys.path.insert(1, os.path.join(os.path.abspath('.'), 'controllers'))
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'controllers'))
import controllers.handlers

# from handlers import SubjectsHandler
from unittest import TestCase

__author__ = 'admin'


class TestSubjectsHandler(TestCase):
    def test_get(self):
        sh = controllers.handlers.SubjectsHandler(self)
        self.assertTrue(sh.get(self), msg="No subjects")

if __name__ == '__main__':
    unittest.main()