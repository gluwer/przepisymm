# coding: utf-8
from google.appengine.ext import db
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
from google.appengine.runtime import DeadlineExceededError
from google.appengine.ext.db import Timeout
from google.appengine.ext import deferred as deferred_lib


from kutils.models import Counter

from przepisy import SHARD_RECIPE_KEY
from przepisy.models import Recipe, RecipeIdx, RecipeFriends
from gfcaccount.utils import get_cached_friends

import logging

def recalculate_views(start_key=None):
  def tx(key, incr):
    recipe = Recipe.get(db.Key(key))
    if recipe:
      recipe.views += incr
      
      to_db = [recipe]
      
      idx = RecipeIdx.get(db.Key.from_path('RecipeIdx', 'idx', parent=recipe.key()))
      if idx:
        idx.views = recipe.views
        to_db.append(idx)

      fri = RecipeFriends.get(db.Key.from_path('RecipeFriends', 'fri', parent=recipe.key()))
      if fri:
        fri.views = recipe.views
        to_db.append(fri)
      
      db.put(to_db)
    
    return True

  while (True):
    try:
      counters = Counter.all()
      if start_key:
        counters.filter('__key__ >', start_key)
      counters.order('__key__')
      counters = counters.fetch(20)
      
      if not counters:
        break
      else:
        start_key = None

      for counter in counters:
        _key = counter.key().name()
        if _key.startswith(SHARD_RECIPE_KEY % u''):
          if db.run_in_transaction(tx, _key.split('|')[1], counter.counter):
            key_tmp = counter.key()
            counter.delete()
            start_key = key_tmp
      
    except (DeadlineExceededError), e:
      deferred_lib.defer(recalculate_views, start_key)
    except (CapabilityDisabledError, Timeout), e:
      break # End if there is no more time...


def update_friends(start_key=None):
  while (True):
    try:
      rec_friends = RecipeFriends.all()
      if start_key:
        rec_friends.filter('__key__ >', start_key)
      rec_friends.order('__key__')
      rec_friends = rec_friends.fetch(20)
      
      if not rec_friends:
        break
      else:
        start_key = None

      for rec_friend in rec_friends:
        rec_friend.friends = get_cached_friends(rec_friend.parent_key().parent().name()).keys()
        rec_friend.put()
        start_key = rec_friend.key()

    except (DeadlineExceededError, Timeout), e:
      deferred_lib.defer(update_friends, start_key)
    except (CapabilityDisabledError), e:
      break # End if there is no more time...
