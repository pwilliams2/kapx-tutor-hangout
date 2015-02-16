# Using redirect route instead of simple routes since it supports strict_slash
# Simple route: http://webapp-improved.appspot.com/guide/routing.html#simple-routes
# RedirectRoute: http://webapp-improved.appspot.com/api/webapp2_extras/routes.html#webapp2_extras.routes.RedirectRoute
from webapp2_extras.routes import RedirectRoute

from controllers import handlers,pages
import utils


secure_scheme = 'https'

_routes = [
    # Retrieve current subject state
    RedirectRoute('/', pages.MainPage, name='main', strict_slash=True),

    RedirectRoute('/admin', pages.AdminPage, name='Admin', strict_slash=True),
    RedirectRoute('/overview', pages.OverviewPage, name='Overview', strict_slash=True),
    RedirectRoute('/analytics', pages.AnalyticsPage, name='Analytics', strict_slash=True),
    RedirectRoute('/reports', pages.ReportCardPage, name='ReportCard', strict_slash=True),
    RedirectRoute('/sessions', pages.SessionsPage, name='Sessions', strict_slash=True),
    RedirectRoute('/surveys', pages.SurveysPage, name='Surveys', strict_slash=True),

    #Tutor Publish
    RedirectRoute('/publishsubjects', handlers.PublishHandler, name='Publish', strict_slash=True),

    # Client Subscribe
    RedirectRoute('/sessions/data', handlers.SessionHandler, name='SessionData', strict_slash=True),
    RedirectRoute('/subscribe', handlers.SubscribeHandler, name='Subscribe', strict_slash=True),
    RedirectRoute('/unsubscribe', handlers.SubscribeHandler, name='Subscribe', strict_slash=True),

    RedirectRoute('/surveys/data', handlers.SurveyHandler, name='Surveys', strict_slash=True),
    RedirectRoute('/subjects', handlers.SubjectsHandler, name='Subjects', strict_slash=True),
    RedirectRoute('/heartbeat', handlers.HeartbeatHandler, name='Heartbeat', strict_slash=True),
    RedirectRoute('/logs', utils.LogPage, name='Logs', strict_slash=True),
    RedirectRoute('/ping', utils.PingHandler, name='ping', strict_slash=True)
]

def get_routes():
    return _routes


def add_routes(app):
    if app.debug:
        secure_scheme = 'http'
    for r in _routes:
        app.router.add(r)
