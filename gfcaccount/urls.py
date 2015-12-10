# -*- coding: utf-8 -*-'gfcaccount/user'
# konto.urls

from werkzeug.routing import (
  Map, Rule, Submount,
  EndpointPrefix, RuleTemplate,
)

def make_rules():
  return [
    EndpointPrefix('gfcaccount/', [
      Rule('/', endpoint='index'),
      Rule('/u/<id>', endpoint='user'),
      Rule('/zaloguj', endpoint='login'),
      Rule('/wyloguj', endpoint='logout'),
    ]),
  ]

all_views = {
  'gfcaccount/index': ('gfcaccount.views.AccountEditHandler', (), {}),
  'gfcaccount/login': 'gfcaccount.views.login',
  'gfcaccount/user': 'gfcaccount.views.user',
  'gfcaccount/logout': 'gfcaccount.views.logout',
}
