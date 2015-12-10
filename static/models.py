# -*- coding: utf-8 -*-
# static.models

from google.appengine.ext import db

class SPage(db.Model):
  title = db.StringProperty(required=True, indexed=False, verbose_name=u'Tytuł')
  meta_desc = db.StringProperty(required=False, indexed=False, verbose_name=u'Opis dla meta')
  body = db.TextProperty(required=True, verbose_name=u'Treść')
  body_html = db.TextProperty(required=False)
  