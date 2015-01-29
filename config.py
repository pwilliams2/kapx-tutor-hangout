import os
from google.appengine.api import app_identity
from google.appengine.ext import ndb

app_name = "KAPx-TUTOR-HANGOUTS"

app_id = app_identity.get_application_id()
isLocal = os.environ.get('SERVER_SOFTWARE', 'Dev').startswith('Dev')

# Environment name constants
ENV_PRODUCTION = 'production'
ENV_DEMO = 'demo'
ENV_DEV = 'development'

environment = "localhost"

def get_path_key():
    try:
        return os.environ['HTTP_HOST'].split(':')[0]
    except KeyError:
        return 'localhost'


def is_env(the_env):
    """Checks the current env against the_env

    Arguments:
      the_env - the environment you want to test against
    """
    return environment == the_env


def is_production():
    """Checks if this environment is production"""
    return is_env(ENV_PRODUCTION)


def is_demo():
    """Checks if this environment is demo"""
    return is_env(ENV_DEMO)


def is_dev():
    """Checks if this environment is dev or local"""
    return isLocal or is_env(ENV_DEV)



error_templates = {
    403: 'errors/default_error.html',
    404: 'errors/default_error.html',
    500: 'errors/default_error.html',
}

# Enable Federated login (OpenID and OAuth)
# Google App Engine Settings must be set to Authentication Options: Federated Login
enable_federated_login = True

# jinja2 base layout templates
base_layout = 'base.html'

STUDENT_ROLE_ID = 2
REGISTRATION_RETRY_COUNT = 1
ALLOW_ACTIVATION_BYPASS = True
RESTRICT_SESSION_JOIN_BY_TIME = False

# Number of minutes before a session start to feature this session as 'NOW LIVE'.  This does NOT affect the users' ability to enter the session, as that is controlled by models.LiveSession.is_live still.
SESSION_ENTER_MINUTES_BEFORE = 30
# Number of minutes after a session ends to feature this session as 'NOW LIVE'.
SESSION_END_MINUTES_AFTER = 0

#: TODO
#  Need to edit /static/social/fblogin.js for each distinct URL...
#  need to refactor this to hit a handler and dynamically map it to a domain-specific file.

# client_code: kapx
# username: kapxadmin
# password: 66D888E3-6C76-4EA3-989A-12317984251E

#: 0=HANGOUT_APP_ID
#: 1=participantToken
HANGOUT_URL_TEMPLATE = 'https://plus.google.com/hangouts/_?gid={0}&gd={1}&hso=0'

# send error emails to developers
send_mail_developer = False

# fellas' list
developers = (
    ('Preston Williams', 'pwilliams2@kaplan.edu')
)

log_email = True


class KapxConfig(ndb.Model):
    pass
#     setting = ndb.StringProperty(required=True)
#     value = ndb.StringProperty(required=True)
#
#     @classmethod
#     def get_config_setting(cls, name, default_value=""):
#         config_setting = cls.query(cls.setting == name).get()
#         if config_setting is None:
#             config_setting = cls(setting=name, value=default_value)
#             config_setting.put()
#         return config_setting
#
#     def __nonzero__(self):
#         """Handle bool contexts
#
#         :return: boolean
#         :rtype: bool
#         """
#         if self.value in [str(False), str(None)]:
#             return False
#         return bool(self.value)
#
# enable_csrf_check = bool(KapxConfig.get_config_setting("enable_csrf_check",
#                                                        default_value="True"))
# # initial value set here but not used here
# KapxConfig.get_config_setting('enable_self_service', default_value='False')
#
# # add all kapx config keys
# webapp2_config['KapxConfig'] = {k.setting: k for k in KapxConfig.query()}
#
# # Set global options for jsonpickle's encoders.
# # http://jsonpickle.github.io/api.html#choosing-and-loading-backends
# import jsonpickle
#
# # fix for https://kss-jira.kaplan.com/browse/KAPX-352 based off of
# # http://stackoverflow.com/questions/7784303/django-escapejs-and-simplejson
# # json encoding does not encode html tags by default so
# # they can break output when used in <script> tags
# # import simplejson.encoder
# # jsonpickle.set_encoder_options('simplejson', cls=simplejson.encoder.JSONEncoderForHTML)
#
# # Badgeville REST api config. Use sandbox if not production
# BADGEVILLE = {
#     'CAIRO': {
#         'subdomain': 'sandbox',
#         # used for Javascript SDK calls
#         'public_key': '9468822b99ef576ffe98add0f163a0ec',
#         # used for REST API calls
#         'private_key': '2283fd34c107d3de2b2a5fa0de3f399b'
#     }
# }
#
#
# SALESFORCE = {
#     'username': 'apiint@kaplan.edu.devfull',
#     'password': 'MWCAPIDev1',
#     'security_token': 'A7qLjgLWv5xcpvjNIWvgpUQVi',
#     'sandbox': True
# }
#
# default_webmail_domain = "gdev.student.kaplan.edu"
#
# # Configuration entries for Tutor.com's LTI SSO Authentication Handler (handlers/TutorLTIHandler)
# tutor_lti_title = 'KAPx-LTI-Tool'
# tutor_lti_launch_url = "http://lhh.tutor.com/LTISSO.aspx"
# tutor_lti_consumer_key = "ZTE5OGVlN2QtZjJkNy00ZjE1LThjYzgtNTQ1NjIyMmVmYTMw"
# tutor_lti_consumer_secret = "WLVwo90ElH/CgxB/FAdz+wp/GPCBfl3TBy7JkcAzwK0="
# tutor_lti_lti_version = "LTI-1p0"
#
# piazza_lti = ('https://piazza.com/connect', 'piazza.sandbox', 'test_only_secret')
#
# echo_domains = None
#
# token_login_shared_secret = 'Shhhh...seKrets...'
# token_login_tolerance_seconds = 30
#
# #: LOCAL ENVIRONMENT overrides all
# if isLocal:
#     #: Local DEV
#
#     # environment this app is running on: localhost, testing, production
#     environment = "localhost"
#
#     KAPX_SITE_URL = 'http://www.kapx.local:8081'
#     API_URL_BASE_VERSION_TEMPLATE = 'http://{0}.kapx.local:8080'
#     API_URL_BASE = 'http://courses.kapx.local:8080'
#     HANGOUT_APP_ID = '173420830464'
#     # API_CLIENT_CODE = 'kapx'
#     # API_USER = "kapx"
#     # API_PASS = "dev"
#     API_CLIENT_CODE = 'kapx'
#     API_USER = "kapx"
#     API_PASS = "66D888E3-6C76-4EA3-989A-12317984251E"
#     session_list_live_client_code = 'KU'
#     session_list_upcoming_client_code = 'Techonomy'
#     live_site_failover_registration = False
#     # live_site_failover_registration_session_id = 'APITest'
#
#     # removed for isLocal
#     google_analytics_code = ""
#
#     identity_login_base_url = "http://auth.kapx.local:9000"
#     kapx_collect_url = "http://collect.kapx.local:8082"
#
#     # Google cloud storage prefix for client large/small images (e.g. /gs/<bucketname>)
#     GCS_CLIENT_IMAGE_PREFIX = '/gs/devel'
#
#     # send error emails to developers
#     send_mail_developer = False
#
#     #webapp2_config['webapp2_extras.sessions']['cookie_args']['secure'] = False
#
#     # Configuration entries for Tutor.com's LTI SSO Authentication Handler (handlers/TutorLTIHandler)
#     tutor_lti_title = 'KAPx-LTI-Tool'
#     tutor_lti_launch_url = "http://lhh.tutor.com/LTISSO.aspx"
#     tutor_lti_consumer_key = "ZTE5OGVlN2QtZjJkNy00ZjE1LThjYzgtNTQ1NjIyMmVmYTMw"
#     tutor_lti_consumer_secret = "WLVwo90ElH/CgxB/FAdz+wp/GPCBfl3TBy7JkcAzwK0="
#     tutor_lti_lti_version = "LTI-1p0"
#
#     LIVE_GCE_PATH = "/_ah/api/kapx/v1"
#     LIVE_GCE_URL = "http://localhost:8080" + LIVE_GCE_PATH
#
# else:
#
#     # Google cloud storage prefix for client large/small images (e.g. /gs/<bucketname>)
#     GCS_CLIENT_IMAGE_PREFIX = '/gs/kapx-publisher-images'
#
#     if app_id == 'kapx-site':
#         #: PROD ENVIRONMENT
#
#         # environment this app is running on: localhost, testing, production
#         environment = ENV_PRODUCTION
#
#         KAPX_SITE_URL = 'https://kapx-site.appspot.com'
#         API_URL_BASE_VERSION_TEMPLATE = 'https://{0}-dot-kapx-live.appspot.com'
#         API_URL_BASE = 'https://kapxlive.kaplan.com'
#         API_CLIENT_CODE = 'kapx'
#         API_USER = "kapx"
#         API_PASS = "66D888E3-6C76-4EA3-989A-12317984251E"
#         HANGOUT_APP_ID = '488710781293'
#         session_list_live_client_code = 'newtuniversity'
#         session_list_upcoming_client_code = 'kapx'
#         live_site_failover_registration = False
#         google_analytics_code = "UA-34027439-2"
#         #kapx.net
#
#         identity_login_base_url = "https://identity.kaplan.com"
#         kapx_collect_url = "https://kapx-collect.appspot.com"
#
#         #: PROD REGISTRATION_FAILOVER ENVIRONMENT
#         # API_URL_BASE = 'https://kapxlive.kaplan.com'
#         # API_CLIENT_CODE = 'kapx'
#         # API_USER = "kapx"
#         # API_PASS = "66D888E3-6C76-4EA3-989A-12317984251E"
#         # session_list_live_client_code = 'newtuniversity'
#         # session_list_upcoming_client_code = 'kapx'
#         # live_site_failover_registration = True
#         # live_site_failover_registration_session_id = 'newtu-we-can-do-better'
#
#         default_webmail_domain = "student.kaplan.edu"
#
#         BADGEVILLE = {
#             'CAIRO': {
#                 'subdomain': 'api.v2',
#                 'public_key': '909e921901d70db4c6c69c5a1eef6e6a',
#                 'private_key': 'd1e8f1783c528e69dadb3f472685bdd0'
#             }
#         }
#
#         SALESFORCE = {
#             'username': 'apiint@kaplan.edu',
#             'password': '8&_78t&*2asY7t7f12sd',
#             'security_token': 'l3s4KvS33ReifP1443mkQJro',
#             'sandbox': False
#         }
#
#         # prod credentials
#         piazza_lti = ('https://piazza.com/connect', 'mountwashington.edu', 'piazza_ns2-4hy5')
#
#         LIVE_GCE_PATH = "/_ah/api/kapx/v1"
#         LIVE_GCE_URL = "https://kapx-live.appspot.com" + LIVE_GCE_PATH
#
#     elif app_id == 'kapx-site-dev':
#         #: DEV ENVIRONMENT
#
#         # environment this app is running on: localhost, testing, production
#         environment = ENV_DEV
#
#         KAPX_SITE_URL = 'https://kapx-site-dev.appspot.com'
#         API_URL_BASE_VERSION_TEMPLATE = 'https://{0}-dot-kapx-live-dev.appspot.com'
#         API_CLIENT_CODE = 'kapx'
#         API_USER = "kapx"
#         API_PASS = "66D888E3-6C76-4EA3-989A-12317984251E"
#         HANGOUT_APP_ID = '678327469949'
#         session_list_live_client_code = 'KU'
#         session_list_upcoming_client_code = 'test_client'
#         google_analytics_code = "UA-34027439-2"
#
#         kapx_collect_url = "https://kapx-collect-dev.appspot.com"
#
#         GCS_CLIENT_IMAGE_PREFIX = '/gs/kapx-publisher-images-dev'
#
#         LIVE_GCE_PATH = "/_ah/api/kapx/v1"
#         LIVE_GCE_URL = "https://kapx-live-dev.appspot.com" + LIVE_GCE_PATH
#
#     elif app_id == 'kapx-site-demo':
#         #: demo ENVIRONMENT
#
#         # environment this app is running on: localhost, testing, production
#         environment = ENV_DEMO
#
#         KAPX_SITE_URL = 'https://kapx-site-demo.appspot.com'
#         API_URL_BASE_VERSION_TEMPLATE = 'https://{0}-dot-kapx-live-demo.appspot.com'
#         API_CLIENT_CODE = 'kapx'
#         API_USER = "kapx"
#         API_PASS = "66D888E3-6C76-4EA3-989A-12317984251E"
#         HANGOUT_APP_ID = '876399041393'
#         session_list_live_client_code = 'KU'
#         session_list_upcoming_client_code = 'test_client'
#         google_analytics_code = "UA-34027439-2"
#
#         kapx_collect_url = "https://kapx-collect-demo.appspot.com"
#
#         SALESFORCE = {
#             'username': 'apiint@kaplan.edu.staging',
#             'password': 'FORC3FULL',
#             'security_token': '0A9qTQOV3w1o9hB3AimJya7j',
#             'sandbox': True
#         }
#
#         GCS_CLIENT_IMAGE_PREFIX = '/gs/kapx-publisher-images-demo'
#
#         LIVE_GCE_PATH = "/_ah/api/kapx/v1"
#         LIVE_GCE_URL = "https://kapx-live-demo.appspot.com" + LIVE_GCE_PATH
#
#     elif app_id == 'kapx-site-qa':
#         #: DEV ENVIRONMENT
#
#         # environment this app is running on: localhost, testing, production
#         environment = "qa"
#
#         API_URL_BASE_VERSION_TEMPLATE = 'https://{0}-dot-kapx-live-qa.appspot.com'
#         API_CLIENT_CODE = 'kapx'
#         API_USER = "KU_SyncLearn_API"
#         API_PASS = "Kaplan123$"
#         session_list_live_client_code = 'KU'
#         session_list_upcoming_client_code = 'test_client'
#         google_analytics_code = "UA-34027439-2"
#
#         kapx_collect_url = "http://collect.kapx.local:8082"
#
#         GCS_CLIENT_IMAGE_PREFIX = '/gs/kapx-publisher-images-demo'
#
#     if environment == ENV_PRODUCTION:
#         echo_domains = ["kapxlive.kaplan.com",
#                         "online.classroom.mountwashington.edu"]
#     else:
#         echo_domains = ["mwo-dot-kapx-live-demo.appspot.com",
#                         "mwo-dot-kapx-live-dev.appspot.com",
#                         "kapx-live-dev.appspot.com",
#                         "kapx-live-demo.appspot.com",
#                         "openlearning-dot-kapx-live-dev.appspot.com",
#                         "openlearning-dot-kapx-live-demo.appspot.com"]