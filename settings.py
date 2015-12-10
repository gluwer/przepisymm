# -*- coding: utf-8 -*-
import os

APP_VERSION = 1

DEFAULT_TIMEZONE = 'Europe/Warsaw'
DEBUG = True
PROFILE = False
SECRET_KEY = 'SECRET TO BE CHANGED'
SESSION_PREFIX = '_gs:'
COOKIE_AGE = 3600
COOKIE_NAME = '_KS'

ADD_APP_PREFIX_TO_KIND = False

ADMINS = ()

TEMPLATE_DIRS = ('templates',)

USE_I18N = True
DEFAULT_LANG = 'pl'
#I18N_DIR = 'i18n'

INSTALLED_APPS = (
    'kay.sessions',
    'kay.auth',
    'gfcaccount',
    'index',
    'static',
    'przepisy',
    'kutils',
    'kay_sitemap'
)

APP_MOUNT_POINTS = {
    'index': '/',
    'static': '/s',
    'gfcaccount': '/konto'
}

CONTEXT_PROCESSORS = (
  'kay.context_processors.request',
  'kay.context_processors.url_functions',
  'kay.context_processors.media_url',
  'gfcaccount.context_processors.gfc_settings',
  'kay_notify.context_processors.notifications',
)

JINJA2_ENVIRONMENT_KWARGS = {
  'autoescape': False,
}

JINJA2_FILTERS = {
  'nl2br': 'kay.utils.filters.nl2br',
  'markdown': 'kutils.text_converters.markdown_filter',
}

MIDDLEWARE_CLASSES = (
  #'appstats.recording.AppStatsDjangoMiddleware',
  'kay.sessions.middleware.SessionMiddleware',
  'kay.auth.middleware.AuthenticationMiddleware',
  'kay_notify.middleware.NotificationsMiddleware',
)
AUTH_USER_BACKEND = 'gfcaccount.backend.GFCBackend'
AUTH_USER_MODEL = 'gfcaccount.models.PMMUser'

MEDIA_URL = '/m/%s' % APP_VERSION

FORMS_USE_XHTML = True

GFC_SITE_ID = 'INSERT ID'
GFC_API_SECRET = 'INSERT SECRET'
DEBUG = False
GFC_API_KEY = '*:' + GFC_SITE_ID
GFC_BASE_DOMAIN = "www.google.com"
GFC_RPC_URL = "http://www.google.com/friendconnect/api/rpc" 
GFC_COOKIE_NAME = "fcauth%s" % GFC_SITE_ID
GFC_SESSION_USER_ID_KEY = 'uid'

SESSION_STORE = 'kay.sessions.sessionstore.SecureCookieSessionStore'

MARKDOWN = {
  'extensions': ['headerid(level=3)', 'tables', u'toc(title=Spis treści)', 'nofollow'], 
  'safe_mode': 'escape'
}

DEFAULT_CACHE_TIME = 300
CACHE_NAMESPACE = '%s' % APP_VERSION

PAGE_SIZE = 20

SITEMAPS = {
  'static': 'index.sitemaps.StaticSitemap',
  'recipes': 'index.sitemaps.RecipesSitemap'
}
