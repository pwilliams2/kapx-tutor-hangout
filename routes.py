# Using redirect route instead of simple routes since it supports strict_slash
# Simple route: http://webapp-improved.appspot.com/guide/routing.html#simple-routes
# RedirectRoute: http://webapp-improved.appspot.com/api/webapp2_extras/routes.html#webapp2_extras.routes.RedirectRoute
from webapp2 import Route
from webapp2_extras.routes import RedirectRoute
from web import handlers
import utils

secure_scheme = 'https'

_routes = [

    # Retrieve current subject state
    RedirectRoute('/', handlers.MainPage, name='main', strict_slash=True),
    RedirectRoute('/sessions', handlers.SessionsPage, name='Sessions', strict_slash=True),

    #Tutor Publish
    RedirectRoute('/publishsubjects', handlers.PublishHandler, name='Publish', strict_slash=True),

    # Client Subscribe
    RedirectRoute('/subscribe', handlers.SubscribeHandler, name='Subscribe', strict_slash=True),
    RedirectRoute('/unsubscribe', handlers.SubscribeHandler, name='Subscribe', strict_slash=True),

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
