from lib.base import BaseHandler
from models.models import *


class AdminPage(BaseHandler):
    def get(self):
        self.render_template('templates/admin.html')


class AnalyticsPage(BaseHandler):
    def get(self):
        self.render_template('templates/analytics.html')


class MainPage(BaseHandler):
    def get(self):
        self.render_template('templates/index.html')


class OverviewPage(BaseHandler):
    def get(self):
        surveys = TutorSurveys.query().order(-TutorSurveys.create_date).fetch(10)
        template_data = {'surveys_query': surveys}
        self.render_template('templates/overview.html', **template_data)


class ReportCardPage(BaseHandler):
    def get(self):
        self.render_template('templates/report_card.html')


class SessionsPage(BaseHandler):
    def get(self):
        """ Get the list of TutorHangoutSessions """
        self.render_template('templates/sessions.html')


class SurveysPage(BaseHandler):
    def get(self):
        self.render_template('templates/surveys.html')


