# -*- coding: utf-8 -*-
# przepisy.deferred

import logging

from google.appengine.ext import db
from google.appengine.ext import deferred

from gfcaccount.models import PMMUser
from gfcaccount.utils import get_cached_friends
from przepisy import models, VISIBILITY

def recipe_update(recipe_key, type, tag_diff=None, category_diff=None, rec_vis_diff=None):
  recipe = models.Recipe.get(recipe_key)
  
  if not recipe:
    raise deferred.PermanentTaskFailure('Recipe key %s no longer exist!' % recipe_key)
  
  if type in ('add', 'enable') and not recipe.disabled:
    def ctx():
      category = models.Category.get_by_key_name(models.CATEGORIES_SV[recipe.category])
      if category:
        category.counter += 1
        category.put()
    
    # dodaj etykiety
    # + AC etykiet
    models.Tag.update_elements(recipe.tags)

    # uaktualnij kategorie
    db.run_in_transaction(ctx)

    # dodaj indeks
    if recipe.rec_vis == VISIBILITY[2]:
      recipe.update_index()
    
    if recipe.rec_vis in (VISIBILITY[1], VISIBILITY[2]):
      recipe.update_friends_idx(get_cached_friends(recipe.parent_key().name()).keys())
  
  if type == 'update' and not recipe.disabled:
    if tag_diff:
      models.Tag.update_elements(*tag_diff)
    
    if rec_vis_diff:
      if recipe.rec_vis == VISIBILITY[2]:
        recipe.update_index()
      elif recipe.rec_vis != VISIBILITY[2] and rec_vis_diff[0] == VISIBILITY[2]:
        recipe.remove_index()
  
      if recipe.rec_vis in (VISIBILITY[1], VISIBILITY[2]):
        recipe.update_friends_idx(get_cached_friends(recipe.parent_key().name()).keys())
  
    if category_diff:
      def ctx1():
        category = models.Category.get_by_key_name(models.CATEGORIES_SV[category_diff[0]])
        if category:
          category.counter -= 1
          if category.counter < 0:
            category.counter = 0          
          category.put()
      db.run_in_transaction(ctx1)
      
      def ctx2():
        category = models.Category.get_by_key_name(models.CATEGORIES_SV[category_diff[1]])
        if category:
          category.counter += 1
          category.put()
      db.run_in_transaction(ctx2)
  
  if type == 'delete' or (type in ('disable', 'update') and recipe.disabled):
    def ctx():
      category = models.Category.get_by_key_name(models.CATEGORIES_SV[recipe.category])
      if category:
        category.counter -= 1
        if category.counter < 0:
          category.counter = 0
        category.put()    
    
    # usuń etykiety
    models.Tag.update_elements(removed=recipe.tags)

    # uaktualnij kategorie
    db.run_in_transaction(ctx)

    # usuń indeks
    if recipe.rec_vis == VISIBILITY[2]:
      recipe.remove_index()

    if recipe.rec_vis in (VISIBILITY[1], VISIBILITY[2]):
      recipe.remove_friends_idx()
    
    # usuń przepis, jeśli usuwanie
    if type == 'delete':
      recipe.delete()
