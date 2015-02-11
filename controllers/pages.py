import json
import datetime

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine import runtime

import tutor_hangouts_api as hapi
from apiclient import discovery
from utils import JSONEncoder, autolog
from lib.base import BaseHandler
from models.models import *


def remove_stale_sessions():
    """ When a tutor closes their H-O, we need to remove them from the available subjects """
    autolog("remove_stale_sessions")
    now = datetime.datetime.now()
    del_list = TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).fetch()

    if del_list and len(del_list) > 0:
        autolog('del_list')
        keys = []
        for item in del_list:
            delta = now - item.last_modified
            if delta.total_seconds() > 60:
                keys.append(item.key)

        if len(keys) > 0:
            autolog('deleting tutor keys ' % keys)
            ndb.delete_multi(keys)


def assign_available_tutors(avail_tutors, subjects_list):
    """ Assign the tutors in the avail_tutors_list to the  subjects
    :param avail_tutors_list: available tutors and their subjects
    :param subjects_list: the tutored subjects
    :return:
    """
    avail_subjects = []
    for tutor in avail_tutors:
        json_tutor_subjects = json.loads(tutor.subjects)
        for tutor_subject in json_tutor_subjects:
            subject = tutor_subject['subject']
            avail_subjects.append(subject)

        done = []  # Subjects that are already updated.
        if len(avail_subjects) == 0:  # No available tutors, so set all subjects to unavailable
            subjects = []
            for subject in subjects_list:
                if subject.subject in done:
                    continue
                subject.is_available = False
                subjects.append(subject)
            ndb.put_multi(subjects)
            break


        for avail_subject in avail_subjects:
            for subject in subjects_list:
                if subject.subject in done:
                    continue

                if avail_subject == subject.subject and tutor.participants_count < tutor.max_participants:
                    subject.gid = tutor.gid
                    subject.is_available = True

                    if avail_subject not in done:
                        done.append(avail_subject)
                else:
                    subject.is_available = False
                    subject.gid = ''

                try:
                    subject.put()
                except OverQuotaError, e:
                    autolog('Over Quota Error, bypassing for now: ' + str(e))


def update_subjects():
    '''Update the subjects table to reflect the availability of the current tutor'''

    subjects_list = HangoutSubjects.query(ancestor=hapi.SUBJECTS_PARENT_KEY).fetch()

    # Retrieve Available Tutors and their subjects
    avail_tutors = TutorSubjects.query(ancestor=hapi.TUTOR_SUBJECTS_PARENT_KEY).fetch()

    if not avail_tutors:  # There are no tutors available
        autolog('No available tutors.')
        for subject in subjects_list:  # Set all subjects to unavailable
            subject.is_available = False
            subject.gid = None
            try:
                subject.put()
            except OverQuotaError, e:
                autolog('Over Quota Error, bypassing for now: ' + str(e))
    else:
        autolog('There are avail_tutors.')
        assign_available_tutors(avail_tutors, subjects_list)


class AdminPage(BaseHandler):
    def get(self):
        self.render_template('templates/admin.html')

class AnalyticsPage(BaseHandler):
    def get(self):
        self.render_template('templates/analytics.html')

class MainPage(BaseHandler):
    def get(self):
        self.render_template('templates/index.html')

class ReportCardPage(BaseHandler):
    def get(self):
        self.render_template('templates/report_card.html')

class SessionsPage(BaseHandler):
    def get(self):
        """ Get the list of TutorHangoutSessions """
        sessions = TutorHangoutSessions.query(ancestor=hapi.TUTOR_SESSIONS_PARENT_KEY).order(-TutorHangoutSessions.start).fetch()

        template_data = {'sessions_query': sessions}
        self.render_template('templates/sessions.html', **template_data)


