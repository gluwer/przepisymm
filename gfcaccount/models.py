# -*- coding: utf-8 -*-
# konto.models

from google.appengine.ext import db

from kay.conf import settings
from kay.utils import (
  crypto, render_to_string, url_for
)
from kay.i18n import lazy_gettext as _

from przepisy import VISIBILITY

class GFCUser(db.Model):
  display_name = db.StringProperty(required=True)
  thumbnail_url = db.StringProperty(required=True, indexed=False)
  is_admin = db.BooleanProperty(required=True, default=False, indexed=False)
  active = db.BooleanProperty(required=True, default=True)
    
  created = db.DateTimeProperty(auto_now_add=True, indexed=False)
  updated = db.DateTimeProperty(auto_now=True, indexed=False)

  def get_url(self):
    return url_for('gfcaccount/user', id=self.key().name())

  def __unicode__(self):
    return unicode(self.display_name)

  def __str__(self):
    return self.__unicode__()

  def is_anonymous(self):
    return False

  def is_authenticated(self):
    return True

  def __eq__(self, obj):
    if not obj:
      return False
    return self.key() == obj.key()

  def __ne__(self, obj):
    return not self.__eq__(obj)


class PMMUser(GFCUser):
  rec_pub = db.IntegerProperty(required=True, default=0, indexed=False)
  rec_vis = db.StringProperty(required=True, indexed=False, choices=VISIBILITY, default=u'Wszystkich', verbose_name=u'Przepisy domyślnie dostępne dla')
  pro_vis = db.StringProperty(required=True, indexed=False, choices=VISIBILITY, default=u'Wszystkich', verbose_name=u'Profil publiczny dostępny dla')

 