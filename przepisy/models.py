# -*- coding: utf-8 -*-
# przepisy.models
import re

from google.appengine.ext import db

from kay.conf import settings
from kay.utils import url_for

from kutils import slugify
from kutils import models as kmodels
from kutils.search import polish_word_segmenter, DELIMETER_REGEXP, FULL_TEXT_STOP_WORDS
from kutils.misc import KeyListProperty

from gfcaccount.models import PMMUser
from gfcaccount.utils import get_cached_user
from przepisy import *

AUTHOR_REGEXP = re.compile('autor:"([^"]+)"', re.UNICODE)
FILTER_REGEXP = re.compile('[a-z]+:"[^"]+"', re.UNICODE)
MULTIWORD_REGEXP = re.compile('"[^"]+"', re.UNICODE)

class Category(db.Model):
  counter = db.IntegerProperty(required=True, default=0)

  def get_url(self, external=False):
    return url_for('przepisy/category', slug=CATEGORIES_VS[self.key().name()], _external=external)

  def __unicode__(self):
    return u'%s (%d)' % (self.key().name(), self.counter)

  @classmethod
  def update(cls, category, inc=1):
    def txn(category, inc):
      element = cls.get_by_key_name(category)
      element.counter += inc
      if element.counter < 0:
        element.counter = 0
      element.put()
      
    try:
      db.run_in_transaction(txn, category, inc)
    except db.TransactionFailedError, e:
      pass # TODO: maybe update it using deferred call?
    
  @classmethod
  def get_for_lists(cls):
    tmp_list = [{'url': c.get_url(), 'name': c.key().name(), 'name_with_count': unicode(c)} for c in cls.all().fetch(20)]
    return sorted(tmp_list, key=lambda k: CATEGORIES_VS[k['name']])

  @classmethod
  def prepopulate(cls):
    for c in CATEGORIES:
      cls.get_or_insert(key_name=c[1])


class TagACIndex(kmodels.ACIndex):
  MIN_CHARS = 2
  MAX_FETCH = 100


class Tag(kmodels.ACEntity):
  INDEX_CLASS = TagACIndex

  slug = db.StringProperty(required=False) # It really is required, but done on put()

  def get_url(self):
    return self.slug

  def put(self):
    if not self.is_saved():
      # TODO: we are risking having the same slug for several props!
      self.slug = slugify(self.key().name())
    super(Tag, self).put()


class IngrACIndex(db.Model):
  idx = db.StringListProperty(required=True)

  MIN_CHARS = 2
  
  @classmethod
  def make_index(cls, value):
    return kmodels.ACIndex.make_index(value)
  
  @classmethod
  def create(cls, value):
    if len(value) < cls.MIN_CHARS:
      return
    
    return cls(key_name=value, idx=cls.make_index(value)) 
  
  @classmethod
  def search(cls, prefix, limit=100):
    indexes = cls.all(keys_only=True).filter('idx =', prefix).order('__key__').fetch(limit)
    
    return [k.name() for k in indexes]


class RecipeIngr(db.Model):
  product = db.StringProperty(required=True)
  portion = db.FloatProperty(required=True)
  weight = db.StringProperty(required=True, choices=PORTION_WEIGHTS, indexed=False)

  def __unicode__(self):
    return u'%s - %.2f (%s)' % (self.product, self.portion, self.weight)


class RecipeIdx(db.Model):
  idx = db.StringListProperty(required=True)
  
  # for sorting only!
  created = db.DateTimeProperty()
  title = db.StringProperty()
  views = db.IntegerProperty()


class RecipeFriends(db.Model):
  friends = db.StringListProperty(required=True)
  
  # for sorting only!
  created = db.DateTimeProperty()
  title = db.StringProperty()
  views = db.IntegerProperty()


class Recipe(db.Model):
  title = db.StringProperty(required=True)
  recipe = db.TextProperty(required=True)
  recipe_html = db.TextProperty(required=True)
  ingr_count = db.IntegerProperty(required=True, default=0, indexed=False)
  
  tags = db.StringListProperty()
  category = db.StringProperty(required=True, choices=CATEGORIES_SV.keys())
  phase = db.StringProperty(required=True, choices=PHASES, indexed=False)
  type = db.StringProperty(required=True, choices=TYPES, indexed=False)
  time = db.IntegerProperty(required=True, choices=TIMES_KEYS, indexed=False)
  ig = db.IntegerProperty(indexed=False)
  rec_vis = db.StringProperty(required=True, choices=VISIBILITY)

  disabled = db.BooleanProperty(required=True, default=False)
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)
  views = db.IntegerProperty(required=True, default=0)

  @property
  def category_display(self):
    return CATEGORIES_SV[self.category]

  @property
  def time_display(self):
    return TIMES_SV[str(self.time)]

  @property
  def author_display(self):
    author = getattr(self, '_cached_author', None)
    
    if not author:
      author = get_cached_user(self.parent_key().name())
      if not author:
        author =  u'Nieznany/odłączony'
      self._cached_author = author
    
    return author

  def get_url(self, external=False):
    return url_for('przepisy/recipe', author=self.parent_key().name(), slug=self.key().name(), _external=external)

  def __unicode__(self):
    return self.title

  def make_index(self):
    idx = polish_word_segmenter.segment(self.title)
    idx.add(self.title.lower().strip())
    
    for x in [x.product for x in RecipeIngr.all().ancestor(self).fetch(20)]:
      idx |= polish_word_segmenter.segment(x)
      idx.add(x.lower().strip())
    
    for x in self.tags:
      idx |= polish_word_segmenter.segment(x)
      idx.add(x.lower().strip())
    
    idx |= set([
      u'autor:"%s"' % self.parent_key().name(),
      u'faza:"%s"' % self.phase,
      u'kategoria:"%s"' % CATEGORIES_SV[self.category],
      u'typ:"%s"' % self.type,
      u'czas:"%s"' % self.time
    ])
    
    idx -= set([u''])
    
    return list(idx)

  def update_index(self):
    RecipeIdx(parent=self, key_name='idx', idx=self.make_index(),
              created=self.created, title=self.title, views=self.views).put()

  def remove_index(self):
    db.delete(db.Key.from_path('RecipeIdx', 'idx', parent=self.key()))

  def update_friends_idx(self, friends):
    RecipeFriends(parent=self, key_name='fri', friends=friends,
              created=self.created, title=self.title, views=self.views).put()

  def remove_friends_idx(self):
    db.delete(db.Key.from_path('RecipeFriends', 'idx', parent=self.key()))

  @classmethod
  def update_views(cls, key, views):
    """Designed to run in cron job!"""
    def tx():
      recipe = cls.get(key)
      recipe.views = views
      idx = RecipeIdx.get(db.Key.from_path('RecipeIdx', 'idx', parent=recipe))
      idx.views = views
      db.put([recipe, idx])
    db.run_in_transaction(tx)
    
  @classmethod
  def search(cls, q, limit=201, order=None, exact=True):
    if not q:
      return []
    
    # Replace last known username with his id or if unknown, pass as user 0
    author_match = AUTHOR_REGEXP.search(q)
    if author_match:
      author = PMMUser.all().filter('display_name =', author_match.group(1)).fetch(1)
      if author:
        q = q.replace(author_match.group(0), u'autor:"%s"' % author[0].key().name())
    
    filters = [f.group(0) for f in FILTER_REGEXP.finditer(q)]
    for f in filters:
      q = q.replace(f, '')
    multi = [multi.group(0)[1:-1].lower() for multi in MULTIWORD_REGEXP.finditer(q)]
    for m in multi:
      q = q.replace(m, '')
    keywords = set(DELIMETER_REGEXP.sub(' ', q).lower().split())
    keywords |= set(multi)
    keywords |= set(filters)

    keywords = filter(lambda x: len(x) >= 2, keywords)
    keywords = list(keywords)[:6] # Only do first 6 to limit filtering/queries
    
    if not keywords:
      return []
    
    if not exact:
      if len(keywords) > 1:
        query = RecipeIdx.all().filter('idx IN', keywords)
      else:
        query = RecipeIdx.all().filter('idx =', keywords[0])
      if order:
        query = query.order(order)
      index_keys = [entry.parent_key() for entry in query.fetch(limit)]
    else:
      if not order:
        query = RecipeIdx.all(keys_only=True)
        for keyword in keywords:
          query = query.filter('idx =', keyword)
        index_keys = [key.parent() for key in query.fetch(limit)]
      else:
        query = RecipeIdx.all()
        for keyword in keywords:
          query = query.filter('idx =', keyword)
        results = query.fetch(limit)
        # Sort in memory...
        _key = order[1:] if order[0] == '-' else order
        _reverse = True if order[0] == '-' else False
        results = sorted(results, key=lambda x: getattr(x, _key), reverse=_reverse)
        index_keys = [entry.parent_key() for entry in results]

    return index_keys


class Favs(db.Model):
  favs = KeyListProperty(Recipe)
  
  @classmethod
  def add_one(cls, user_key, recipe_key):
    favs = cls.get_or_insert('favs', parent=user_key, favs=[])
    if recipe_key not in favs.favs:
      favs.favs.insert(0, recipe_key)
      favs.favs = favs.favs[:20]
      favs.put()
    
  @classmethod
  def remove_one(cls, user_key, recipe_key):
    favs = cls.get(db.Key.from_path(cls.__name__, 'favs', parent=user_key))
    if favs and recipe_key in favs.favs:
      favs.favs.remove(recipe_key)
      if len(favs.favs) > 0:
        favs.put()
      else:
        favs.delete()
  
  @classmethod
  def is_a_fave(cls, user_key, recipe_key):
    favs = cls.get(db.Key.from_path(cls.__name__, 'favs', parent=user_key))
    if favs and recipe_key in favs.favs:
      return True
    else:
      return False
    
  @classmethod
  def get_list(cls, user_key):
    favs = cls.get(db.Key.from_path(cls.__name__, 'favs', parent=user_key))
    if favs:
      ret = Recipe.get(favs.favs)
      return [r for r in ret if r is not None]
    else:
      return []
