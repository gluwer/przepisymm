# -*- coding: utf-8 -*-
# gfcaccount.views

import logging

from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest
)

from kay.utils import (
  render_to_response, reverse,
  get_by_key_name_or_404, get_by_id_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)
from kay.i18n import gettext as _
from babel.dates import format_date
from kay.conf import settings

from kutils.cache import cache_get, cache_set
from kutils.handlers import LoginRequiredHandler
from gaefy.db.pager import PagerQuery


from przepisy import VISIBILITY, models
from gfcaccount.forms import AccountEditForm
from gfcaccount.utils import get_cached_user, is_my_friend


class AccountEditHandler(LoginRequiredHandler):
  def prepare(self):
    self.form = AccountEditForm(self.request.user)

  def get(self):
    return render_to_response('gfcaccount/index.html', {
      'form': self.form.as_widget(),
      'info': {
        'name': self.request.user.display_name,
        'public_recipes': self.request.user.rec_pub,
        'join_date': format_date(self.request.user.created, format='long', locale='pl')
      }
    })

  def post(self):
    if self.form.validate(self.request.form):
      try:
        self.form.save()
        cache_set(self.request.user, 'gfcu', self.request.user.key().name())
      
        self.request.notifications.success('Zmiany zapisane!')
        return redirect(url_for('gfcaccount/index'))
      except Exception, e:
        logging.exception('Account edit save failed: ' + str(e))
        self.request.notifications.error('Zmian nie zapisano! Błąd zapisu, spróbuj później...')
        return redirect(url_for('gfcaccount/index'))        
    else:
      self.request.notifications.error(u'Zmian nie zapisano! Formularz zawiera błędy.')
    return self.get()


def login(request):
  if request.user.is_authenticated():
    url = request.args.get('next', '/')
    redirect(url if url.startswith('/') else '/')
  return render_to_response('gfcaccount/login.html', {})
  

def logout(request):
  return render_to_response('gfcaccount/logout.html', {})


def user(request, id):
  user = get_cached_user(id)
  if not user:
    return NotFound()
    
  if not user.active:
    return render_to_response('gfcaccount/private.html', {'active': False})

  if (user.pro_vis == VISIBILITY[0] and request.user.key().name() != id) or (user.pro_vis == VISIBILITY[1] and not is_my_friend(request.user.key().name(), id)):
    return render_to_response('gfcaccount/private.html', {'active': True})
    
  # pobierz przepisy użytkownika
  prev, recipes, next = PagerQuery(models.Recipe) \
    .ancestor(user) \
    .filter('disabled =', False) \
    .filter('rec_vis =', VISIBILITY[2]) \
    .order('-created') \
    .fetch(settings.PAGE_SIZE, request.args.get('b', None))
  
  if request.is_xhr:
    return render_to_response('przepisy/includes/public_list.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
      'user_id': id,
    })
  else:
    return render_to_response('gfcaccount/public.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
      'user_id': id,
      'info': {
        'name': user.display_name,
        'public_recipes': user.rec_pub,
        'join_date': format_date(user.created, format='long', locale='pl'),
        'thumbnail': user.thumbnail_url,
      }
    })