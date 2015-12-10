# coding: utf-8
from google.appengine.ext import db

from kutils.cache import cache_set, cache_get
from kutils.oshelpers import get_user_friends, get_user_profile, is_friend_of

from gfcaccount.models import PMMUser

def get_cached_friends(user_id):
  friends = cache_get('gfcf', user_id)
  
  if not friends:
    _friends = get_user_friends(user_id)
    if _friends:
      friends = {}
      for friend in _friends:
        friends[friend['id']] = {'id': friend['id'], 'displayName': friend['displayName'], 'thumbnailUrl': friend['thumbnailUrl']}
    else:
      friends = {}
    cache_set(friends, 'gfcf', user_id)
  
  return friends
  

def get_cached_is_friend(user_id, friend_id):
  is_friend = cache_get('gfcuf', user_id, friend_id)
  
  if not is_friend:
    is_friend = is_friend_of(user_id, friend_id)
    if is_friend:
      is_friend = 'y'
    else:
      is_friend = 'n'
    cache_set(is_friend, 'gfcuf', user_id, friend_id)
  
  return is_friend == 'y'


def is_my_friend(user_id, friend_id):
  return get_cached_is_friend(user_id, friend_id)


def get_cached_user(user_id):
  user = cache_get('gfcu', user_id)

  if not user:
    _user = get_user_profile(user_id)
    if _user:

      def txn():
        entity = PMMUser.get_by_key_name(user_id)
        if entity is None:
          entity = PMMUser(
              key_name=uid,
              display_name=_user.get_display_name(),
              thumbnail_url=_user.get('thumbnailUrl')
          )
          entity.put()
        else:
          entity.display_name = _user.get_display_name()
          entity.thumbnail_url = _user.get('thumbnailUrl')
          entity.put()
        return entity
      
      # Do update in transaction only if you really have to...
      user = PMMUser.get_by_key_name(user_id)
      if not user:
        user = db.run_in_transaction(txn)
      elif user.thumbnail_url != _user.get('thumbnailUrl') or user.display_name != _user.get_display_name():
        user = db.run_in_transaction(txn)

      cache_set(user, 'gfcu', user_id)
    else:
      user = None
    
  return user  
