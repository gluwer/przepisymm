#!/usr/bin/env python

from urlparse import urlsplit, urlunsplit

from google.appengine.ext import db
from werkzeug.utils import import_string

from kay.exceptions import ImproperlyConfigured
from kay.conf import settings
from kay.auth.models import AnonymousUser

from kutils.cache import cache_get, cache_set

class GFCBackend(object):
  def get_user(self, request):
    try:
      auth_model_class = import_string(settings.AUTH_USER_MODEL)
    except (ImportError, AttributeError), e:
      raise ImproperlyConfigured, \
          'Failed to import %s: "%s".' % (settings.AUTH_USER_MODEL, e)
    
    # Check if fcauth cookie exists and if not, use anonymous and return
    fcauth = request.cookies.get(settings.GFC_COOKIE_NAME, None)
    if not fcauth:
      # Remove the uid if not logged in
      request.session.pop(settings.GFC_SESSION_USER_ID_KEY, None)
      return AnonymousUser()
    
    fcuser = None
    
    # Check in session if user_id is there, if yes, load and return
    uid = request.session.get(settings.GFC_SESSION_USER_ID_KEY, None)
    if not uid:
      # The uid not in session, must get data using OpenSocial call
      from kutils.oshelpers import get_current_user_profile
      fcuser = get_current_user_profile(fcauth)
      
      # If fcuser empty, treat as not logged in
      if not fcuser:
        return AnonymousUser()
      else: # Set uid in variable and in session
        uid = fcuser.get_id()
        request.session[settings.GFC_SESSION_USER_ID_KEY] = uid
        update_user = True
    
    user = cache_get('gfcu', uid)
    if user and user.active:
      return user
    elif user and not user.active:
      return AnonymousUser()
    else:
      # Make sure that profile data are up to date
      if not fcuser:
        from kutils.oshelpers import get_current_user_profile
        fcuser = get_current_user_profile(fcauth)
        
        if not fcuser:
          return AnonymousUser()
        
      def txn():
        entity = auth_model_class.get_by_key_name(uid)
        if entity is None:
          entity = auth_model_class(
              key_name=uid,
              display_name=fcuser.get_display_name(),
              thumbnail_url=fcuser.get('thumbnailUrl')
          )
          entity.put()
        else:
          entity.display_name = fcuser.get_display_name()
          entity.thumbnail_url = fcuser.get('thumbnailUrl')
          entity.put()
        return entity
      
      # Do update in transaction only if you really have to...
      user = auth_model_class.get_by_key_name(uid)
      if not user:
        user = db.run_in_transaction(txn)
      elif user.thumbnail_url != fcuser.get('thumbnailUrl') or user.display_name != fcuser.get_display_name():
        user = db.run_in_transaction(txn)
      
      cache_set(user, 'gfcu', uid)
      return user

  def create_login_url(self, url):
    local_url = urlsplit(url)
    local_url = urlunsplit(('', '', local_url.path, local_url.query, local_url.fragment))
    
    from kay.utils import url_for
    return url_for("gfcaccount/login", next=local_url)

  def create_logout_url(self, url):
    local_url = urlsplit(url)
    local_url = urlunsplit(('', '', local_url.path, local_url.query, local_url.fragment))
    
    from kay.utils import url_for
    return url_for("gfcaccount/logout", next=local_url)

  def login(self, request, user_name, password):
    return