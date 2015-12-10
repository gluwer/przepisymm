# coding: utf-8
# KeyListProperty is borrowed from App Engine Patch project (MIT licensed)
# EtagProperty & PickleProperty are borrowed from aetycoon project (licensd on ?)

import hashlib
import pickle
import logging

from google.appengine.ext import db

from google.appengine.ext.deferred import defer, run, PermanentTaskFailure
from google.appengine.runtime import DeadlineExceededError

from kutils.cache import cache_get, cache_delete

class KeyListProperty(db.ListProperty):
	"""Simulates a many-to-many relation using a list property.
	
	On the model level you interact with keys, but when used in a ModelForm
	you get a ModelMultipleChoiceField (as if it were a ManyToManyField)."""

	def __init__(self, reference_class, *args, **kwargs):
		self._reference_class = reference_class
		super(KeyListProperty, self).__init__(db.Key, *args, **kwargs)

	def validate(self, value):
		new_value = []
		for item in value:
			if isinstance(item, basestring):
				item = db.Key(item)
			if isinstance(item, self._reference_class):
				item = item.key()
			if not isinstance(item, db.Key):
				raise db.BadValueError('Value must be a key or of type %s' %
									   self.reference_class.__name__)
			new_value.append(item)
		return super(KeyListProperty, self).validate(new_value)

class EtagProperty(db.Property):
	"""Automatically creates an ETag based on the value of another property.

	Note: the ETag is only set or updated after the entity is saved.

	Example usage:

	.. code-block:: python

	   from google.appengine.ext import db
	   from tipfy.ext.db import EtagProperty

	   class StaticContent(db.Model):
		   data = db.BlobProperty()
		   etag = EtagProperty(data)
	"""
	def __init__(self, prop, *args, **kwargs):
		self.prop = prop
		super(EtagProperty, self).__init__(*args, **kwargs)

	def get_value_for_datastore(self, model_instance):
		v = self.prop.__get__(model_instance, type(model_instance))
		if not v:
			return None

		if isinstance(v, unicode):
			v = v.encode('utf-8')

		return hashlib.sha1(v).hexdigest()


def render_json_response(obj):
	import simplejson
	from werkzeug import Response
	
	return Response(simplejson.dumps(obj), mimetype='application/json')


def get_reference_key(model, prop):
	return getattr(model.__class__, prop).get_value_for_datastore(model)


class Mapper(object):
  """A base class to process all entities in single datastore kind, using
  the task queue. On each request, a batch of entities is processed and a new
  task is added to process the next batch.

  For example, to delete all 'MyModel' records:
  .. code-block:: python

   from tipfy.ext.taskqueue import Mapper
   from mymodels import myModel

   class MyModelMapper(EntityTaskHandler):
     model = MyModel

     def map(self, entity):
       # Add the entity to the list of entities to be deleted.
       return ([], [entity])

   mapper = MyModelMapper()
   deferred.defer(mapper.run)

  Mapper class for task queue. Borrowed from tipfy framework.
  """
  # Subclasses should replace this with a model class (eg, model.Person).
  model = None

  # Subclasses can replace this with a list of (property, value) tuples
  # to filter by.
  filters = []

  def __init__(self):
    self.to_put = []
    self.to_delete = []

  def map(self, entity):
    """Updates a single entity.

    Implementers should return a tuple containing two iterables
    (to_update, to_delete).
    """
    return ([], [])

  def finish(self):
    """Called when the mapper has finished, to allow for any final work to
    be done.
    """
    pass

  def get_query(self):
    """Returns a query over the specified kind, with any appropriate filters
    applied.
    """
    q = self.model.all()
    for prop, value in self.filters:
      q.filter('%s =' % prop, value)

    q.order('__key__')
    return q

  def run(self, batch_size=20):
    """Starts the mapper running."""
    self._continue(None, batch_size)

  def _batch_write(self):
    """Writes updates and deletes entities in a batch."""
    if self.to_put:
      db.put(self.to_put)
      self.to_put = []

    if self.to_delete:
      db.delete(self.to_delete)
      self.to_delete = []

  def _continue(self, start_key, batch_size):
    """Processes a batch of entities."""
    q = self.get_query()
    # If we're resuming, pick up where we left off last time.
    if start_key:
      q.filter('__key__ >', start_key)

    # Keep updating records until we run out of time.
    try:
      # Steps over the results, returning each entity and its index.
      for i, entity in enumerate(q):
        map_updates, map_deletes = self.map(entity)
        self.to_put.extend(map_updates)
        self.to_delete.extend(map_deletes)

      # Do updates and deletes in batches.
      if (i + 1) % batch_size == 0:
         self._batch_write()

         # Record the last entity we processed.
         start_key = entity.key()

    except DeadlineExceededError:
      # Write any unfinished updates to the datastore.
      self._batch_write()
      # Queue a new task to pick up where we left off.
      defer(self._continue, start_key, batch_size)
      return

    self.finish()


def incrementCounter(key, property="counter", update_interval=10):
  """Increments a memcached counter.
  Args:
    key: The key of a datastore entity that contains the counter.
    update_interval: Minimum interval between updates.
  """
  lock_key = "icl:%s" % key
  count_key = "icv:%s" % key
  if cache_add(None, lock_key, time=update_interval):
    # Time to update the DB
    count = int(cache_get(count_key) or 0) + 1
    def tx():
      entity = db.get(key)
      setattr(entity, property, getattr(entity, property) + count)
      entity.put()
    db.run_in_transaction(tx)
    cache_delete(count_key)
  else:
    # Just update memcache
    cache_incr(1, count_key, initial_value=0)
