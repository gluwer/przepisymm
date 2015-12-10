# -*- coding: utf-8 -*-
"""
Sample usage:

def make_rules():
  return [
    EndpointPrefix('sitemap/', [
      Rule('/sitemap.xml', endpoint='index'),
      Rule('/sitemap-<section>.xml', endpoint='sitemap'),
    ]),
  ]

all_views = {
  'sitemap/index': 'kay_sitemap.views.index',
  'sitemap/sitemap': 'kay_sitemap.views.sitemap',
}

In settings.py there should be a:
SITEMAPS = {
  'static': 'index.sitemaps.StaticSitemap',
}
"""
from werkzeug.routing import (
  Map, Rule, Submount,
  EndpointPrefix, RuleTemplate,
)

def make_rules():
  return []

