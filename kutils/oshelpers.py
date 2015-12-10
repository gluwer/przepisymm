# coding: utf-8
import logging
import opensocial

from kay.conf import settings

# Friend check extension
class CheckFriendConnectionRequest(opensocial.Request):
  """ A request for creating an activity. """
  def __init__(self, user_id, friend_id):
    params = {"command":"AreFriends", "params": {"friendA":user_id, "friendB":friend_id}}
    rpc_request = opensocial.RpcRequestInfo('extensions.get', params=params)
    super(CheckFriendConnectionRequest, self).__init__(None, rpc_request)
    
  def process_json(self, json):
    return json


def get_current_user_profile(fcauth, fields=None):
  config = opensocial.ContainerConfig(server_rpc_base=settings.GFC_RPC_URL, security_token=fcauth, security_token_param='fcauth')
  container = opensocial.ContainerContext(config)

  try:
    user = container.fetch_person(fields=fields)
  except:
    logging.exception("Problem getting the viewer")
    user = None

  return user


def get_user_profile(user_id, fields=None):
  config = opensocial.ContainerConfig(server_rpc_base=settings.GFC_RPC_URL, oauth_consumer_key=settings.GFC_API_KEY, oauth_consumer_secret=settings.GFC_API_SECRET)
  container = opensocial.ContainerContext(config)

  try:
    user = container.fetch_person(user_id, fields=fields)
  except:
    logging.exception("Problem getting user %s" % user_id)
    user = None

  return user


def create_activity(user_id, title, body):
  config = opensocial.ContainerConfig(server_rpc_base=settings.GFC_RPC_URL, oauth_consumer_key=settings.GFC_API_KEY, oauth_consumer_secret=settings.GFC_API_SECRET)
  container = opensocial.ContainerContext(config)

  activity = opensocial.Activity({})
  activity['title'] = title
  activity['body'] = body

  try:
    request = opensocial.CreateActivityRequest(user_id, activity)
    response = container.send_request(request)
  except:
    logging.exception("Problem sending activity %s" % title)
    raise


def get_user_friends(user_id, fields=None):
  config = opensocial.ContainerConfig(server_rpc_base=settings.GFC_RPC_URL, oauth_consumer_key=settings.GFC_API_KEY, oauth_consumer_secret=settings.GFC_API_SECRET)
  container = opensocial.ContainerContext(config)
  
  try:
    request = opensocial.FetchPeopleRequest(user_id, '@friends', fields=fields, params={'count': 100})
    friends = container.send_request(request)
  except:
    logging.exception("Problem getting the info about friends of user %s" % user_id)
    friends = []

  return friends


def is_friend_of(user_id, friend_id):
  if user_id == friend_id:
    return True
  
  config = opensocial.ContainerConfig(server_rpc_base=settings.GFC_RPC_URL, oauth_consumer_key=settings.GFC_API_KEY, oauth_consumer_secret=settings.GFC_API_SECRET)
  container = opensocial.ContainerContext(config)
  
  try:
    request = CheckFriendConnectionRequest(user_id, friend_id)
    friends = container.send_request(request)
    is_friend = friends['value']
  except:
    logging.exception("Problem getting the info about friendness of users %s and %s" % (user_id, friend_id))
    is_friend = False

  return is_friend
