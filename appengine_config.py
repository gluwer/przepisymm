import kay
kay.setup_syspath()

##### appstats configuration #####

appstats_MAX_STACK = 6  # Max number of stack frames per call to record.
appstats_MAX_LOCALS = 10  # Max number of locals per frame to record.
appstats_MAX_REPR = 100  # Max output string length of format_value().
appstats_MAX_DEPTH = 10  # Max depth for format_value().
appstats_TZOFFSET = 0
appstats_LOCK_TIMEOUT = 1

# normalize_path() takes a path and returns an 'path key'.  The path
# key is used by the UI to compute statistics for similar URLs.  If
# your application has a large or infinite URL space (e.g. each issue
# in an issue tracker might have its own numeric URL), this function
# can be used to produce more meaningful statistics.

def appstats_normalize_path(path):
  return path

# extract_key() is a lower-level function with the same purpose as
# normalize_key().  It can be used to lump different request methods
# (e.g. GET and POST) together, or conversely to use other information
# on the request object (mostly the query string) to produce a more
# fine-grained path key.  The argument is a StatsProto object; this is
# a class defined in recording.py.  Useful methods are:
#
#   - http_method()
#   - http_path()
#   - http_query()
#   - http_status()
#
# Note that the StatsProto argument is loaded only with summary
# information; this means you cannot access the request headers.

def appstats_extract_key(request):
  key = appstats_normalize_path(request.http_path())
  if request.http_method() != 'GET':
    key = '%s %s' % (request.http_method(), key)
  return key