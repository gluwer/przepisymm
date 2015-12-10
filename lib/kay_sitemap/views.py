# -*- coding: utf-8 -*-
import logging

from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest
)
from werkzeug.utils import import_string

from kay.utils import (
  render_to_response, reverse, render_to_string,
  get_by_key_name_or_404, get_by_id_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)

from kay.conf import settings


def index(request):
  sites = []
  for section in settings.SITEMAPS.keys():
    sites.append(url_for('sitemap/sitemap', section=section, _external=True))
  xml = render_to_string('kay_sitemap/sitemap_index.xml', {'sitemaps': sites})
  return Response(xml, mimetype='application/xml')

def sitemap(request, section=None):
  logging.info('ff')
  if section is not None:
    if section not in settings.SITEMAPS:
      return NotFound("No sitemap for section: %s" % section)
  else:
    return NotFound()
  logging.info('zz')
  sitemap = import_string(settings.SITEMAPS[section])()

  xml = render_to_string('kay_sitemap/sitemap.xml', {'urlset': sitemap.get_urls()})
  return Response(xml, mimetype='application/xml')