# -*- coding: utf-8 -*-
# index.urls


from werkzeug.routing import (
  Map, Rule, Submount,
  EndpointPrefix, RuleTemplate,
)

def make_rules():
  return [
    EndpointPrefix('index/', [
      Rule('/', endpoint='index'),
    ]),
    EndpointPrefix('sitemap/', [
      Rule('/sitemap.xml', endpoint='index'),
      Rule('/sitemap-<section>.xml', endpoint='sitemap'),
    ]),
  ]

all_views = {
  'index/index': 'index.views.index',
  'sitemap/index': 'kay_sitemap.views.index',
  'sitemap/sitemap': 'kay_sitemap.views.sitemap',
}
