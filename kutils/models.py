# coding: utf-8
import random
from google.appengine.ext import db

from kay.utils import crypto
from kay.models import NamedModel

from kutils.search import polish_word_segmenter

class KeyedModel(NamedModel):
  @classmethod
  def get_key_generator(cls, **kwargs):
    while 1:
      yield crypto.gen_random_identifier()


class ACIndex(db.Model):
  idx = db.StringListProperty(required=True)
  order = db.IntegerProperty(required=True, default=0)

  MIN_CHARS = 3
  
  @classmethod
  def make_index(cls, value):
    # Add whole sentence
    final_idx = [value[:x] for x in range(cls.MIN_CHARS, len(value)+1)]
    
    # Do segmenting and remove first word
    words = polish_word_segmenter.segment(value)
    words -= set([value.split()[0]])
    for word in words:
      final_idx.extend((word[:x] for x in range(cls.MIN_CHARS, len(word)+1)))
    
    return final_idx
  
  @classmethod
  def create(cls, parent, value, order=0):
    if len(value) < cls.MIN_CHARS:
      return
    
    return cls(key_name='idx', parent=parent, order=order, idx=cls.make_index(value)) 
  
  @classmethod
  def search(cls, prefix, only_key_names=True, order='-order', limit=100):
    indexes = cls.all(keys_only=True).filter('idx =', prefix).order(order).fetch(limit)
    
    if only_key_names:
      return [k.parent().name() for k in indexes]
    else:
      parents = [k.parent() for k in indexes]
      return db.get(parents)


class ACEntity(db.Model):
  counter = db.IntegerProperty(required=True, default=0)

  INDEX_CLASS = ACIndex

  def __unicode__(self):
    return u'%s (%d)' % self.key().name(), self.counter

  @classmethod
  def find_differences(cls, old, new):
    old_s = set(old)
    new_s = set(new)
    added = list(new_s - old_s)
    removed = list(old_s - new_s)
    return added, removed
  
  @classmethod
  def split_elements(cls, elements):
    return [e.strip() for e in elements.lower().split(u',') if e.strip() != '']
  
  @classmethod
  def update_elements(cls, added=[], removed=[]):
    def txn(name, inc):
      element = cls.get_by_key_name(name)
      if inc:
        if element is None:
          element = cls(key_name=name)
          element.counter = 1
          element.put()
          cls.INDEX_CLASS.create(element, name, element.counter).put()
        else:
          element.counter += 1
          
          elementAC = cls.INDEX_CLASS.all().ancestor(element).get()
          keys = [element]
          if elementAC:
            elementAC.order = element.counter
            keys.append(elementAC)
          db.put(keys)
      else:
        if element is None:
          return
        
        element.counter -= 1
        keys = [element]
        
        elementAC = cls.INDEX_CLASS.all().ancestor(element).get()
        if elementAC:
          keys.append(elementAC)
          
        if element.counter <= 0:
          db.delete(keys)
        else:
          if elementAC:
            keys[1].order = element.counter
          db.put(keys)

    for name in added:
      try:
        db.run_in_transaction(txn, name, True)
      except db.TransactionFailedError, e:
        pass # TODO: add it to deferred call
    for name in removed:
      try:
        db.run_in_transaction(txn, name, False)
      except db.TransactionFailedError, e:
        pass # TODO: add it to deferred call


# Below code is inspired by GaeGene shared counters package licensed under Apache 2.
# It was simplified (no cache) and changed to class methods to be extensible if needed.
# In addition it was optimized to take less space in Datastore.
class CounterConfig(db.Model):
  shards = db.IntegerProperty(required=False, default=1)


class Counter(db.Model):
  counter = db.IntegerProperty(required=True, default=0)

  @classmethod
  def count(cls, name):
    config = CounterConfig.get_by_key_name(name)
    if not config:
      return 0
    
    count = 0
    for counter in cls.get([db.Key.from_path(cls.kind(), "%s|%s" % (name, shard)) for shard in range(1, config.shards+1)]):
      count += counter.counter
    
    return int(count)
  
  @classmethod
  def incr_txn(cls, name, delta, config):
    shard = random.randint(1, config.shards)
    shard_key_name = "%s|%s" % (name, shard)
    
    counter = cls.get_by_key_name(shard_key_name)
    if counter is None:
      counter = cls(key_name=shard_key_name)
    
    counter.counter += delta
    counter.put()
  
  @classmethod
  def add_txn(cls, name, shards):
    config = CounterConfig.get_by_key_name(name)
    
    if shards > 0:
      config.shards += shards
      config.put()
    
    return config.shards

  @classmethod
  def incr(cls, name, delta=1):
    config = CounterConfig.get_by_key_name(name)
    db.run_in_transaction(cls.incr_txn, name, delta, config)
        
  @classmethod
  def max_shards(cls, name):
    config = CounterConfig.get_by_key_name(name)
    return config.shards

  @classmethod
  def init_shards(cls, name, shards):
    CounterConfig(key_name=name, shards=shards).put()
    
  @classmethod
  def add_shards(cls, name, shards):
    return db.run_in_transaction(cls.add_txn, name, shards)

  @classmethod
  def remove_by_name(cls, name):
    config = CounterConfig.get_by_key_name(name)
    to_remove = [db.Key.from_path(cls.kind(), "%s|%s" % (name, shard)) for shard in range(1, config.shards+1)]
    to_remove.append(config.key())
    db.delete(to_remove)

