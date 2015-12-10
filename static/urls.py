# -*- coding: utf-8 -*-
# static.urls


from werkzeug.routing import (
  Map, Rule, Submount,
  EndpointPrefix, RuleTemplate,
)

def make_rules():
  return [
    EndpointPrefix('static/', [
      Rule('/<slug>', endpoint='page'),
    ]),
  ]

all_views = {
  'static/page': ('static.views.StaticPageHandler', (), {}),
}
