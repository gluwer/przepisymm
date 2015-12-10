# -*- coding: utf-8 -*-
# static.views

import logging

from google.appengine.api import users
from google.appengine.api import memcache
from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest, Unauthorized
)

from kay.utils import (
  render_to_response, reverse,
  get_by_key_name_or_404, get_by_id_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)
from kay.i18n import gettext as _
from kay.auth.decorators import login_required
from kay.handlers import BaseHandler

from kutils.text_converters import markdown2html

from static.models import SPage
from static.forms import SPageForm


class StaticPageHandler(BaseHandler):
  def admin_get(self, slug):
    page = SPage.get_by_key_name(slug)
    if page:
      form = SPageForm(page)
    else:
      form = SPageForm()    
    
    return render_to_response('static/edit.html', {
      'form': form.as_widget(),
    })

  def get(self, slug):
    if self.request.user.is_authenticated() and self.request.user.is_admin:
      if self.request.args.get('edit', False):
        return self.admin_get(slug)
      else:
        edit = True
    else:
      edit = False
    
    page = get_by_key_name_or_404(SPage, slug)
    return render_to_response('static/page.html', {
      'page': page,
      'edit': edit,
    })

  def post(self, slug):
    if self.request.user.is_anonymous() or not self.request.user.is_admin:
      return Unauthorized()
    
    page = SPage.get_by_key_name(slug)
    if page:
      form = SPageForm(page)
    else:
      form = SPageForm()
    
    if form.validate(self.request.form):
      try:
        SPage(key_name=slug, title=form['title'], meta_desc=form['meta_desc'],
              body=form['body'], body_html=markdown2html(form['body'])
        ).put()
      
        self.request.notifications.success('Strona zapisana!')
        return redirect(self.request.base_url)
      except Exception, e:
        logging.exception('Static page save failed: ' + str(e))
        self.request.notifications.error('Zmian nie zapisano! Błąd zapisu.')
        return redirect(self.request.base_url)        
    else:
      self.request.notifications.error(u'Zmian nie zapisano! Formularz zawiera błędy.')
    
    return render_to_response('static/edit.html', {
      'form': form.as_widget(),
    })    
