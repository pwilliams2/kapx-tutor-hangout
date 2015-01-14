import datetime
import json
import logging
import time

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import ndb, db
from webapp2_extras.appengine.auth.models import User as AuthUser

import lib.timezone
from .signals import pre_put, post_put
import lib.preferences as preflib


class BaseModel(ndb.Model):
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        pre_put.send(sender=self.__class__, model_inst=self)
    
    def _post_put_hook(self, future):
        self.is_saved = True
        post_put.send(sender=self.__class__, model_inst=self)

    @property
    def get_id(self):
        return self.key.id()

    @classmethod
    def get_by_ids(cls, ids):
        """Gets a list of items by ID

        :param ids: The ids to fetch
        :type ids: list of str
        :return: A collection of entities
        :rtype: list of cls
        """
        return ndb.get_multi([ndb.Key(cls._get_kind(), _id) for _id in ids])

    def to_json(self, include=None, exclude=None):
        """JSONifies the model"""
        # setup date serialization
        def data_type_handler(obj):
            if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
                return str(long(time.mktime(obj.timetuple())))
            elif isinstance(obj, db.IntegerProperty):
                return str(obj) if obj != None else "0"
            elif isinstance(obj, db.FloatProperty):
                return str(obj) if obj != None else "0"
            elif isinstance(obj, ndb.Key):
                child = obj.get()
                if child:
                    if obj.kind() == "User":
                        return ""
                return {"id": obj.id()}
            elif isinstance(obj, ndb.BlobKey):
                return str(obj)
            # elif isinstance(obj, ndb.Blob):
                # return obj
            else:
                return None

        #gets the model's dict
        model_dict = self.to_dict(include = include, exclude = exclude)
        model_dict.update({"id": self.get_id})
        # dumps json for our dict object
        result = json.dumps(model_dict, default=data_type_handler, indent = 4)
        return result


class User(AuthUser):
    """
    Universal user model. Can be used with App Engine's default users API,
    own auth or third party authentication methods (OpenID, OAuth etc).
    based on https://gist.github.com/kylefinley
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #: User defined unique name, also used as key_name.
    # Not used by OpenID
    username = ndb.StringProperty()
    #: User Name
    name = ndb.StringProperty()
    #: User Last Name
    last_name = ndb.StringProperty()
    #: User email
    email = ndb.StringProperty()
    #: Hashed password. Only set for own authentication.
    # Not required because third party authentication
    # doesn't use password.
    password = ndb.StringProperty()
    #: User Country
    country = ndb.StringProperty()
    #: Account activation verifies email
    activated = ndb.BooleanProperty(default=False)
    #: Determines whether or not the user can access administrative pages.
    is_admin = ndb.BooleanProperty(default=False)

    #: Records the user agreeing to terms and conditions
    agree_to_terms = ndb.BooleanProperty(default=False)

    #: Records the user's preference to receive promotional emails.
    promo_emails = ndb.BooleanProperty(default=True)

    # a list of clients that the user has permissions to admin
    client_permission = ndb.StringProperty()

    # temp storage for player id
    badgeville_player_id = ndb.JsonProperty('bvid', default={})

    # User was found as a lead or contact in salesforce
    in_salesforce = ndb.BooleanProperty()

    # webmail email address
    webmail_address = ndb.StringProperty()

    # block the user from login?
    blocked = ndb.BooleanProperty(default=False)

    #throw here whatever extra info you want for the user
    extra_info = ndb.JsonProperty('bvid', default={})

    # NOTE: this is to ensure that all of the User.kapx_id accesses don't
    # bomb out if the user doesn't have an explicitly set kapx_id.
    kapx_id = ndb.ComputedProperty(lambda self: self.key.id())

    @classmethod
    def get_by_email(cls, email):
        """Returns a user object based on an email.

        :param email:
            String representing the user email. Examples:

        :returns:
            A user object.
        """
        return cls.query(cls.email == email).get()

    @classmethod
    def get_by_guid(cls, guid):
        """Returns a user object based on a guid.

        :param guid:
            String representing the user guid. Examples:

        :returns:
            A user object.
        """
        user_key = ndb.Key('User', guid)

        return user_key.get()

    @classmethod
    def get_key(cls, guid):
        user_key = ndb.Key('User', guid)
        return user_key

    def get_social_providers_names(self):
        social_user_objects = SocialUser.get_by_user(self.key)
        result = []
        #import logging
        for social_user_object in social_user_objects:
            #logging.error(social_user_object.extra_data['screen_name'])
            result.append(social_user_object.provider)
        return result

    def get_social_providers_info(self):
        providers = self.get_social_providers_names()
        result = {'used': [], 'unused': []}
        for k, v in SocialUser.PROVIDERS_INFO.items():
            if k in providers:
                result['used'].append(v)
            else:
                result['unused'].append(v)
        return result

    @classmethod
    def list(cls):
        return cls.query(cls.activated == True).order(cls.last_name, cls.name).fetch()

    def is_client_admin(self, client_code):
        # if there is no client_permission set, we grant global permission
        client_match = True

        if self.client_permission:
            client_match = client_code in self.client_permission.split(",")

        return self.is_admin and client_match

    @property
    def _mc_key(self):
        return 'preferences_%s' % self.kapx_id

    def _mc_get(self):
        return memcache.get(self._mc_key) or {}

    def _mc_set(self, prefcache):
        memcache.set(self._mc_key, prefcache)

    def preferences(self):
        """Gets user preferences

        :return: The dict of user settings in {setting: value} format
        :rtype: dict
        """
        _prefcache = self._mc_get()
        if self.kapx_id not in _prefcache:
            _prefcache[self.kapx_id] = preflib.preferences(self.kapx_id)
            self._mc_set(_prefcache)
        return _prefcache[self.kapx_id]

    def set_preference(self, name, value):
        """Sets a global user preference value

        :param name: The preference name
        :type name: str
        :param value: The preference value
        :type value: object
        :return: The dict of user settings in {setting: value} format
        :rtype: dict
        """
        if value != self.preference(name):
            _prefcache = self._mc_get()
            _prefcache[self.kapx_id] = preflib.set_preference(self.kapx_id, name, value)
            self._mc_set(_prefcache)
        return self.preferences()

    def preference(self, name, default=None):
        """Gets the value of a user preference

        :param name: The preference name
        :type name: str
        :param default: Default value if not set
        :type default: object
        :return: The dict of user settings in {setting: value} format
        :rtype: dict
        """
        return self.preferences().get(name, default)

    def client_preferences(self, client):
        """Gets all client preferences for this user

        :param client: The client whose preference it is
        :type client: models.models.LiveClient
        :return: The dict of user settings in {setting: value} format
        :rtype: dict
        """
        _prefcache = self._mc_get()
        if client.client_code not in _prefcache:
            _prefcache[client.client_code] = preflib.client_preferences(self.kapx_id, client)
            self._mc_set(_prefcache)
        return _prefcache[client.client_code]

    def set_client_preference(self, client, name, value):
        """Sets a client preference value

        :param client: The client whose preference it is
        :type client: models.models.LiveClient
        :param name: The preference name
        :type name: str
        :param value: The preference value
        :type value: object
        :return: The dict of user settings in {setting: value} format
        :rtype: dict
        """
        if value != self.client_preference(client, name):
            _prefcache = self._mc_get()
            _prefcache[client.client_code] = preflib.set_client_preference(self.kapx_id, client, name, value)
            self._mc_set(_prefcache)
        return self.client_preferences(client)

    def client_preference(self, client, name, default=None):
        """Gets the value of a client preference for this user

        :param client: The client whose preference it is
        :type client: models.models.LiveClient
        :param name: The preference name
        :type name: str
        :param default: Default value if not set
        :type default: object
        :return: The dict of user settings in {setting: value} format
        :rtype: dict
        """
        return self.client_preferences(client).get(name, default)


class LogVisit(BaseModel):
    user = ndb.KeyProperty(kind=User)
    uastring = ndb.StringProperty()
    ip = ndb.StringProperty()
    timestamp = ndb.StringProperty()


class LogEmail(BaseModel):
    sender = ndb.StringProperty(
        required=True)
    to = ndb.StringProperty(
        required=True)
    subject = ndb.StringProperty(
        required=True)
    body = ndb.TextProperty()
    when = ndb.DateTimeProperty()


class SocialUser(BaseModel):
    PROVIDERS_INFO = {  # uri is for OpenID only (not OAuth)
        'google': {'name': 'google', 'label': 'Google', 'uri': 'gmail.com'},
        'facebook': {'name': 'facebook', 'label': 'Facebook', 'uri': ''},
    }
    '''
    PROVIDERS_INFO = {  # uri is for OpenID only (not OAuth)
        'google': {'name': 'google', 'label': 'Google', 'uri': 'gmail.com'},
        'facebook': {'name': 'facebook', 'label': 'Facebook', 'uri': ''},
    }
    PROVIDERS_INFO = { # uri is for OpenID only (not OAuth)
        'google': {'name': 'google', 'label': 'Google', 'uri': 'gmail.com'},
        'facebook': {'name': 'facebook', 'label': 'Facebook', 'uri': ''},
        'linkedin': {'name': 'linkedin', 'label': 'LinkedIn', 'uri': ''},
        'myopenid': {'name': 'myopenid', 'label': 'MyOpenid', 'uri': 'myopenid.com'},
        'twitter': {'name': 'twitter', 'label': 'Twitter', 'uri': ''},
        'yahoo': {'name': 'yahoo', 'label': 'Yahoo!', 'uri': 'yahoo.com'},
    }
    '''

    user = ndb.KeyProperty(kind=User)
    provider = ndb.StringProperty()
    uid = ndb.StringProperty()
    extra_data = ndb.JsonProperty()

    @classmethod
    def get_by_user(cls, user):
        return cls.query(cls.user == user).fetch()

    @classmethod
    def get_by_user_and_provider(cls, user, provider):
        return cls.query(cls.user == user, cls.provider == provider).get()

    @classmethod
    def get_by_provider_and_uid(cls, provider, uid):
        return cls.query(cls.provider == provider, cls.uid == uid).get()

    @classmethod
    def check_unique_uid(cls, provider, uid):
        # pair (provider, uid) should be unique
        test_unique_provider = cls.get_by_provider_and_uid(provider, uid)
        if test_unique_provider is not None:
            return False
        else:
            return True

    @classmethod
    def check_unique_user(cls, provider, user):
        # pair (user, provider) should be unique
        test_unique_user = cls.get_by_user_and_provider(user, provider)
        if test_unique_user is not None:
            return False
        else:
            return True

    @classmethod
    def check_unique(cls, user, provider, uid):
        # pair (provider, uid) should be unique
        return cls.check_unique_uid(provider, uid)

    @staticmethod
    def open_id_providers():
        return [k for k, v in SocialUser.PROVIDERS_INFO.items() if v['uri']]



class LMSInstance(ndb.Model):
    name = ndb.StringProperty(required=True) # typically the hostname
    auth_token = ndb.StringProperty(required=True)
    lti_provider_base_url = ndb.StringProperty(required=True)
    lti_consumer_key = ndb.StringProperty(required=True)
    lti_consumer_secret = ndb.StringProperty(required=True)
    lti_version = ndb.StringProperty(required=True)
    lti_launch_url = ndb.StringProperty(required=True)
    sso_type = ndb.StringProperty()
    sso_options_json = ndb.StringProperty()
    
    @classmethod
    @ndb.transactional
    def create(cls, **fields):
        ent_id = fields['name']
        key = ndb.Key(cls, ent_id)
        if key.get() is not None:
            raise IntegrityError('Already existing id=%s' % ent_id)
        ent = cls(**fields)
        ent.key = key
        ent.put()
        return ent


class IntegrityError(Exception):
    pass


class LMSInstanceMembership(BaseModel):
    """M2M relationship between LiveSession and LMSInstance"""
    lms_course_id = ndb.StringProperty(required=True)
    lms_instance_id = ndb.KeyProperty(LMSInstance)


class LiveSession(BaseModel):

    SYNC = 1
    ASYNC = 2
    SESSION_TYPES = {SYNC: u'Synchronous', ASYNC: u'Asynchronous'}
    OPEN = 1
    RESTRICTED = 2
    ACCESS_TYPES = {OPEN: u'1', RESTRICTED: u'2'}

    #: Unique Session ID to use in identifying this LiveSession in Kapx-Live
    live_session_id = ndb.StringProperty(required=True)
    #client_code = ndb.KeyProperty(kind=LiveClient)
    client_code = ndb.StringProperty(required=True)

    title = ndb.StringProperty(required=True)
    # Thumbnail image for use in the catalog *list* view
    thumbnail_url = ndb.StringProperty()
    # Short description (html) for use in the catalog *list* view
    short_description = ndb.TextProperty()
    # Summary description (html) for use in the new catalog *list* view
    summary = ndb.StringProperty()
    # Session detail page content (html)
    description = ndb.TextProperty()
    # Course Code for this session (optional)
    course_code = ndb.StringProperty()
    # third party ID for this session (optional)
    external_id = ndb.StringProperty()
    session_thumb = ndb.StringProperty()
    session_thumb_alt = ndb.StringProperty()
    # Type of LiveSession this is...Synchronous are standard sessions...
    # Asynchronous are courses, effectively.
    session_type = ndb.IntegerProperty(choices=SESSION_TYPES.keys(),
                                       default=SYNC)
    # Start date and time of the session (optional...display purposes only)
    start = ndb.DateTimeProperty()
    # End date and time of the session (optional...display purposes only)
    end = ndb.DateTimeProperty()
    is_trial = ndb.BooleanProperty(default=False)
    activation_required = ndb.BooleanProperty(default=True)
    is_published = ndb.BooleanProperty(default=False)
    is_live = ndb.BooleanProperty(default=False)
    archived = ndb.BooleanProperty(default=False)
    moderated = ndb.BooleanProperty(default=True)
    # flag to turn registration form on/off
    is_registration_form_active = ndb.BooleanProperty(default=False)

    # Registration Form definition
    registration_form = ndb.TextProperty()
    seo_title = ndb.StringProperty()
    seo_description = ndb.TextProperty()

    has_challenge_exam = ndb.BooleanProperty(default=False)

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    # LMS instances in which this course appears
    lms_instances = ndb.StructuredProperty(LMSInstanceMembership, repeated=True)

    layout = ndb.StringProperty(default='1')             # default layout of the event/session would be first one
    access_type = ndb.IntegerProperty(choices=ACCESS_TYPES.keys(), default=OPEN)
    waiting_room_duration = ndb.StringProperty(default='15')

    #throw here whatever extra info you want for the Session
    extra_settings = ndb.JsonProperty(default={})

    def get_session_type_display(self):
        sess_type = self.session_type or self.SYNC
        return self.SESSION_TYPES.get(sess_type)

    def get_event_type(self):
        try:
            # Database times are stored in EST...datetime.now returns UTC.
            now = lib.timezone.localize_utc_to_eastern(datetime.datetime.now())
            now_notz = now.replace(tzinfo=None)

            if (self.is_live):
                if (self.end and self.end > now_notz):
                    return 'live'

            if (self.start and self.start > now_notz):
                return 'upcoming'

            return ''
        except Exception, e:
            logging.exception(e)
            return ''
    
    def get_lms_course_id(self, lms_instance_id=None):
        """This only makes sense for async LiveSessions"""
        if lms_instance_id is None:
            client = LiveClient.get_by_id(self.client_code)
            lms_instance_id = client.lms_instance and client.lms_instance.id()
        if lms_instance_id:
            for lms_inst in self.lms_instances:
                if lms_inst.lms_instance_id.id() == lms_instance_id:
                    return lms_inst.lms_course_id
        return None
    
    def set_lms_course_id(self, lms_course_id, lms_instance_id=None):
        """This only makes sense for async LiveSessions"""
        if lms_instance_id is None:
            client = LiveClient.get_by_id(self.client_code)
            if not client.lms_instance:
                raise ValueError('You should either pass `lms_instance_id` '
                     'param or assign a LMSInstance model to LiveClient(%s)'
                     % self.client_code)
            lms_instance_id = client.lms_instance
        else:
            lms_instance_id = LMSInstance.get_by_id(lms_instance_id).key
        to_add = LMSInstanceMembership(lms_course_id=str(lms_course_id),
                                       lms_instance_id=lms_instance_id)
        if not to_add in self.lms_instances:
            self.lms_instances.append(to_add)
        self.put()
    
    @property
    def is_joinable(self):
        try:
            return self.is_live
        except Exception, e:
            logging.error('is_joinable threw an exception accessing self.is_live')
            logging.exception(e)
            return False

    @classmethod
    def list(cls, client_code=None, session_type=None, archived=None):
        query = cls.query()
        if archived is not None:
            query = cls.filter(cls.archived == archived)
        if client_code:
            query = query.filter(cls.client_code == client_code)
        if session_type is not None:
            query = query.filter(cls.session_type == session_type)
        return query.fetch()

    @classmethod
    def get_by_external_id(cls, external_id):
        return cls.query(cls.external_id == external_id).get()

    def populate_from(self, _dict, skip=()):
        props = set(self._properties.keys()) - set(skip)
        fields = {f: v for f, v in _dict.items() if f in props}
        super(LiveSession, self).populate(**fields)
    
class LiveSessionAnnouncement(BaseModel):
    creator_display = ndb.StringProperty()
    body = ndb.TextProperty(required=True)

    @classmethod
    def add_by_parent(cls, parent_key, creator_display, body):
        return cls(parent=parent_key, creator_display=creator_display, body=body).put()

    @classmethod
    def get_by_ancestor(cls, ancestor_key, wanted=1):
        return cls.query(ancestor=ancestor_key).order(-cls.created_at).fetch(wanted)

    @classmethod
    @ndb.synctasklet
    def get_by_ancestor_async(cls, ancestor_key, wanted=1):
        announcements = yield cls.query(ancestor=ancestor_key).order(-cls.created_at).fetch_async(wanted)
        yield ndb.get_multi_async([announcement.key for announcement in announcements])
        raise ndb.Return(announcements)


class UserLiveSession(BaseModel):

    STATUS_HOLD = 'hold'
    STATUS_OK = 'ok'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_DROP = 'drop'
    STATUS_COMPLETED = 'completed'

    ROLE_INSTRUCTOR = 1
    ROLE_STUDENT = 2
    ROLE_MODERATOR = 3
    ROLE_ADMINISTRATOR = 4
    ROLE_NAMES = {ROLE_INSTRUCTOR: 'Instructor',
                  ROLE_STUDENT: 'Student',
                  ROLE_MODERATOR: 'Moderator',
                  ROLE_ADMINISTRATOR: 'Administrator'}

    @classmethod
    def role_name(cls, role_id):
        try:
            return cls.ROLE_NAMES[role_id]
        except KeyError:
            pass

    user = ndb.KeyProperty(kind=User)
    live_session = ndb.KeyProperty(kind=LiveSession)
    registration_form_response = ndb.JsonProperty()  # Registration Form definition
    #: This is the accessToken from the kapx-live site when the user registers for a LiveSession.
    access_token = ndb.StringProperty(required=True)
    ip_address = ndb.StringProperty(required=True)
    estimated_start = ndb.DateProperty()
    estimated_end = ndb.DateProperty()
    term_id = ndb.StringProperty()  # used to associate with an external term structure since kapx does not have that
    restrict_start = ndb.DateTimeProperty()
    restrict_end = ndb.DateTimeProperty()
    registration_status = ndb.StringProperty(default=STATUS_OK, choices=[STATUS_OK, STATUS_HOLD, STATUS_DROP,
                                                                         STATUS_COMPLETED, STATUS_SCHEDULED])

    role_id = ndb.IntegerProperty(default=ROLE_STUDENT)

    @classmethod
    def list(cls, user):
        query = cls.query(UserLiveSession.user == user.key).order(UserLiveSession.live_session)
        return query.fetch()

    @classmethod
    def get_for_user_and_session(cls, user, live_session, term_id=None):
        query = cls.query(cls.live_session == live_session.key,
                          cls.user == user.key)
        if term_id:
            query = query.filter(cls.term_id == term_id)
        return query.get()

    @classmethod
    def fetch_for_user_role(cls, user_or_id, live_session_or_id, role_id):
        """Gets a list of any UserLiveSession objects matching the given role id"""
        live_session_key = live_session_or_id.key if hasattr(live_session_or_id, 'key') \
            else ndb.Key(LiveSession, live_session_or_id)
        user_key = user_or_id.key if hasattr(user_or_id, 'key') else ndb.Key(User, user_or_id)
        query = cls.query(cls.live_session == live_session_key,
                          cls.user == user_key,
                          cls.role_id == role_id)
        return list(query)

    @classmethod
    def fetch_with_user_faculty_roles(cls, user_or_id):
        """Gets a list of any UserLiveSession objects where the user is a faculty role

        :rtype: list of UserLiveSession
        """
        user_key = user_or_id.key if hasattr(user_or_id, 'key') else ndb.Key(User, user_or_id)
        query = cls.query(cls.user == user_key, cls.role_id != cls.ROLE_STUDENT)
        return list(query)

    @classmethod
    def fetch_for_user(cls, user_or_id):
        """Gets a list of any UserLiveSession objects for a user

        :rtype: list of UserLiveSession
        """
        user_key = user_or_id.key if hasattr(user_or_id, 'key') else ndb.Key(User, user_or_id)
        query = cls.query(cls.user == user_key)
        return list(query)

    @property
    def is_joinable(self):
        within_time_window = True
        now = datetime.datetime.now()
        if (self.restrict_start and self.restrict_start > now) or (self.restrict_end and self.restrict_end < now):
            within_time_window = False
        return within_time_window and self.registration_status == self.STATUS_OK

    def is_student(self):
        return self.role_id == UserLiveSession.ROLE_STUDENT

    def is_moderator(self):
        return self.role_id == UserLiveSession.ROLE_MODERATOR

    def is_instructor(self):
        return self.role_id == UserLiveSession.ROLE_INSTRUCTOR


class LiveClient(BaseModel):
    client_code = ndb.StringProperty()
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    description = ndb.StringProperty()
    featured = ndb.BooleanProperty(default=False)
    order = ndb.IntegerProperty(default=0)
    payment_public_key = ndb.StringProperty()
    payment_secret_key = ndb.StringProperty()
    large_image = ndb.StringProperty()
    small_image = ndb.StringProperty()
    badgeville_site_id = ndb.StringProperty('bv')
    register_leads_in_salesforce = ndb.BooleanProperty('add_sf')
    self_enrollment_url = ndb.StringProperty()
    sender_email = ndb.StringProperty()
    recipient_email = ndb.StringProperty()
    contact_email = ndb.StringProperty(default="kapx@kaplan.com")
    webmail_domain = ndb.StringProperty()
    webmail_org_unit = ndb.StringProperty()
    has_campaign_tracking = ndb.BooleanProperty(default=False)

    #Private Clients will not show up in Kapx-default
    private = ndb.BooleanProperty(default=False)
    lms_instance = ndb.KeyProperty('LMSInstance')
    nickname = ndb.StringProperty()

    @classmethod
    def _get_by_id(cls, id, parent=None, **ctx_options):
        """Get by ID or nickname"""
        client = cls.query(cls.nickname == id).get()
        if client:
            return client
        return cls._get_by_id_async(id, parent=parent, **ctx_options).get_result()
    get_by_id = _get_by_id
    
    @classmethod
    def get_by_user_permission(cls, user):
        clients_filter = user.client_permission
        if clients_filter:
            clients_list = clients_filter.split(',')
            clients = cls.query(cls.client_code.IN(clients_list)).fetch()
        else:
            clients = cls.query().fetch()

        return clients

    @property
    def lms_instance(self):
        return self.remote_info.get('lms_instance')

    @webapp2.cached_property
    def remote_info(self):
        try:
            from lib.clients.clients import get_remote_info
            return get_remote_info(self)
        except:
            return {}


class CampaignTracking(BaseModel):
    campaign_source = ndb.StringProperty(required=True)
    user_info_request = ndb.StringProperty(repeated=True)
    template_name = ndb.StringProperty()
    events = ndb.StringProperty(repeated=True)

class LiveUser(object):
    username = ''
    email = ''


class SalesforceUserEnrollmentStatus(ndb.Model):
    user = ndb.KeyProperty(kind=User, required=True)
    completed = ndb.BooleanProperty(default=False)
    success = ndb.BooleanProperty()
    messages = ndb.TextProperty(repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def enrollment_id(self):
        return self.key.id()

    @classmethod
    def create_enrollment(cls, enrollment_id, user_or_kapx_id):
        user_key = getattr(user_or_kapx_id, 'key', None) or User.get_by_id(user_or_kapx_id).key
        enroll = cls(id=enrollment_id, user=user_key)
        enroll.put()
        return enroll


class HostnameThemeMap(ndb.Model):
    client_key = ndb.KeyProperty(kind=LiveClient, required=True)
    theme_name = ndb.StringProperty(required=True)

    @property
    def hostname(self):
        return self.key.id()

    @property
    def client(self):
        return self.client_key.get()

    @property
    def client_code(self):
        return self.client.client_code

    @classmethod
    def create(cls, hostname, client, force_theme=None):
        """Creates a new mapping entry

        This will overwrite existing hostname entries since that is the key

        :param hostname: The hostname to map
        :type hostname: str
        :param client: Client who's theme to show
        :type client: LiveClient
        :param force_theme: Theme name to use if not client_code
        :type force_theme: str or None
        :return: The entity
        :rtype: HostnameThemeMap
        """
        theme = cls(id=hostname.lower(), client_key=client.key,
                    theme_name=force_theme or client.client_code)
        theme.put()
        return theme

    @classmethod
    def set_multi(cls, hostname_list, client):
        """Sets the current maps for a client

        This will overwrite any existing hostnames since it uses HostnameThemeMap.create internally

        :param hostname_list: List of HTTP Hosts to map
        :type hostname_list: list
        :param client: Client who's theme to show
        :type client: LiveClient
        :return: The new entities
        :rtype: list of HostnameThemeMap
        """
        to_delete = [m.key for m in cls.fetch_for_client(client) if m.hostname not in hostname_list]
        if to_delete:
            ndb.delete_multi(to_delete)
        # let them overwrite in case the details changed from what was currently saved?
        return [cls.create(hostname, client) for hostname in hostname_list]

    @classmethod
    def get_for_hostname(cls, hostname):
        """Gets the mapping for a hostname if present

        :param hostname: HTTP host to search for
        :type hostname: str
        :return: The mapping
        :rtype: HostnameThemeMap
        """
        return cls.get_by_id(hostname)

    @classmethod
    def fetch_for_client(cls, client):
        """Fetches all hostname maps for a client

        :param client: The client
        :type client: LiveClient
        :return: The mapping objects
        :rtype: list of HostnameThemeMap
        """
        return cls.query(cls.client_key == client.key)


class EmbeddedPage(BaseModel):
    """Model to store embedded external pages that should be iframed into KAPx"""
    # client code this page belongs to
    client_code = ndb.StringProperty(required=True)
    # page title for <title>
    page_title = ndb.StringProperty(required=True)
    # iframe src value
    iframe_url = ndb.StringProperty(required=True)
    # stores verbatim attr="value" data to add to the <iframe> tag
    iframe_attrs = ndb.TextProperty()

    def _pre_put_hook(self):
        super(EmbeddedPage, self)._pre_put_hook()
        # always override key using page_id so we can add entities via datastore viewer
        self._key = ndb.Key(self._get_kind(), str(self.page_id))

    @property
    def page_id(self):
        return self.key.id()

    @classmethod
    def create(cls, client_or_code, page_id, page_title, iframe_url, iframe_attrs=None):
        client = client_or_code if hasattr(client_or_code, 'key') else LiveClient.get_by_id(client_or_code)
        page = cls(id=page_id, client_code=client.client_code,
                   page_title=page_title,
                   iframe_url=iframe_url, iframe_attrs=iframe_attrs)
        page.put()
        return page

    @classmethod
    def find_by_client(cls, client_or_code):
        if hasattr(client_or_code, 'key'):
            client_or_code = client_or_code.key.get().client_code
        return cls.query(cls.client_code == client_or_code).fetch()

    @classmethod
    def get_by_client_and_id(cls, client_or_code, page_id):
        if hasattr(client_or_code, 'key'):
            client_or_code = client_or_code.key.get().client_code
        page = cls.get_by_id(page_id)
        if page.client_code == client_or_code:
            return page
