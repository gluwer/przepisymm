# -*- coding: utf-8 -*-
# index.views

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
from kay.auth.decorators import login_required

from przepisy import VISIBILITY
from przepisy.models import Category, Recipe, Favs
from static.models import SPage

def index(request):
  if request.user.is_authenticated():
    favs = Favs.get_list(request.user.key())
  else:
    favs = None
  
  return render_to_response('index/index.html',{
    'categories': Category.get_for_lists(),
    'hpinfo': SPage.get_by_key_name('hpinfo'),
    'new_recipes': Recipe.all().filter('rec_vis =', VISIBILITY[2]).filter('disabled =', False).order('-created').fetch(10),
    'pop_recipes': Recipe.all().filter('rec_vis =', VISIBILITY[2]).filter('disabled =', False).order('-views').fetch(10),
    'fav_recipes': favs,
  })
