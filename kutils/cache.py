# coding: utf-8

# Part of this code comes from thechowdown-appengine example:
# http://code.google.com/p/google-friend-connect-samples
# Copyright 2009 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");

import logging
from google.appengine.api import memcache
from google.appengine.ext import db

from kay.conf import settings
 
def cache_set(data, *args, **kwargs):
  """ Sends an object to a memory cache."""
  time = settings.DEFAULT_CACHE_TIME if not kwargs.has_key("time") else kwargs["time"]
  memcache.set("|".join(args), data, time, namespace=settings.CACHE_NAMESPACE)
  return data

def cache_multiset(data_dict, time=settings.DEFAULT_CACHE_TIME):
  """ Sends multiple objects to a memory cache."""
  data = {}
  for k, v in data_dict:
    data[k if isinstance(k, basestring) else "|".join(k)] = v
  memcache.set_multi(data, time, namespace=settings.CACHE_NAMESPACE)
  return data_dict

def cache_get(*args):
  """ Gets an object from a memory cache."""
  data = memcache.get("|".join(args), namespace=settings.CACHE_NAMESPACE)
  return data

def cache_multiget(key_list):
  data = memcache.get_multi([(k if isinstance(k, basestring) else "|".join(k)) for k in key_list], namespace=settings.CACHE_NAMESPACE)
  return data

def cache_delete(*args):
  """ Deletes an object from a memory cache."""
  return memcache.delete("|".join(args))

def cache_multidelete(key_list):
  return memcache.delete_multi([(k if isinstance(k, basestring) else "|".join(k)) for k in key_list], namespace=settings.CACHE_NAMESPACE)

def cache_add(data, *args, **kwargs):
  """ Adds an object to a memory cache."""
  time = settings.DEFAULT_CACHE_TIME if not kwargs.has_key("time") else kwargs["time"]
  return memcache.add("|".join(args), data, time, namespace=settings.CACHE_NAMESPACE)

def cache_incr(delta=1, *args, **kwargs):
  """ Increments a counter in memory cache."""
  initial_value = 0 if not kwargs.has_key("initial_value") else kwargs["initial_value"]
  return memcache.incr("|".join(args), delta, namespace=settings.CACHE_NAMESPACE, initial_value=initial_value)

##### Decorators #####

def cache(key_format, time=settings.DEFAULT_CACHE_TIME):
  """ Decorator which caches the result of the method which it decorates.
  
  Stores the output of the method this decorates in memcache. Based off of the
  pattern submitted by bcannon (modified by jorisp) at http://is.gd/6rAw
  
  Args: 
    key_format: A string containing placeholder tokens in the form of %s.  
        Tokens will be substituted with the values of any non-keyword arguments
        to the decorated method, in the order in which they appear.  If the
        argument is a data store object, its data store key will be used as 
        the token replacement.
    time: Optional argument specifying how long in seconds the result should
        be cached for.
    
  Returns:
    The result of calling the decorated method with the supplied arguments,
    from the cache if available, otherwise, from calling the method directly.
  """
  def method_decorator(method):
    def method_wrapper(*args, **kwargs):
      key_args = []
      for arg in args[0:key_format.count('%')]:
        if hasattr(arg, "key") and hasattr(arg.key(), "id_or_name"):
          key_args.append(arg.key().id_or_name())
        else:
          key_args.append(str(arg))
      data = cache_get(key_format % tuple(key_args), namespace=settings.CACHE_NAMESPACE)
      if data:
        return data
      data = method(*args, **kwargs)
      return cache_set(key, data, time, namespace=settings.CACHE_NAMESPACE)
    return method_wrapper
  return method_decorator

