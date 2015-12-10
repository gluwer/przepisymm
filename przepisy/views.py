# -*- coding: utf-8 -*-
# przepisy.views

import logging
import datetime
import math

from google.appengine.ext import db
from google.appengine.api import memcache, users
from google.appengine.ext import deferred as deferred_lib
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
from google.appengine.runtime import DeadlineExceededError

from werkzeug import (
  unescape, redirect, Response,
)
from werkzeug.exceptions import (
  NotFound, MethodNotAllowed, BadRequest, Unauthorized
)

from kay.utils import (
  render_to_response, reverse,
  get_by_key_name_or_404, get_by_id_or_404, get_or_404,
  to_utc, to_local_timezone, url_for, raise_on_dev
)
from kay.i18n import gettext as _
from kay.auth.decorators import login_required, admin_required
from kay.conf import settings
from kay.cache.decorators import no_cache
from kay.sessions.decorators import no_session
from gaefy.db.pager import PagerQuery
from werkzeug.contrib.atom import AtomFeed
from jinja2.utils import escape

from kutils import slugify
from kutils.cache import cache_get, cache_set, cache_delete
from kutils.handlers import LoginRequiredHandler
from kutils.text_converters import markdown2html
from kutils.oshelpers import create_activity
from kutils.models import Counter, CounterConfig
from kutils.misc import render_json_response

from gfcaccount.models import PMMUser
from gfcaccount.utils import is_my_friend, get_cached_friends

from przepisy.forms import RecipeForm
from przepisy import models, deferred, VISIBILITY, SHARD_RECIPE_KEY, ORDERINGS
from przepisy.utils import recalculate_views, update_friends



class RecipeAddHandler(LoginRequiredHandler):
  def prepare(self):
    initial = {}
    initial['rec_vis'] = self.request.user.rec_vis
    self.form = RecipeForm(initial)

  def get(self):
    return render_to_response('przepisy/add.html', {
      'form': self.form.as_widget(),
    })

  def post(self):
    if self.form.validate(self.request.form):
      try:
        # utwórz przepis
        recipe = models.Recipe(
          parent=self.request.user,
          key_name=slugify(self.form['title']),
          title=self.form['title'],
          recipe=self.form['recipe'],
          recipe_html=markdown2html(self.form['recipe']),
          tags=models.Tag.split_elements(self.form['tags']),
          category=self.form['category'],
          phase=self.form['phase'],
          type=self.form['type'],
          ig=self.form['ig'],
          time=int(self.form['time']),
          rec_vis=self.form['rec_vis'],
          ingr_count=len(self.form['ingr']),
          disabled=False
        )
        
        # zapisz dane przepisu
        recipe.put()
        
        # dodaj osobno skladniki
        # + AC składników
        ingr_to_save = []
        for i, ingr in enumerate(self.form['ingr']):
          ingr_to_save.append(models.RecipeIngr(parent=recipe, key_name='%2d'%(i+1), product=ingr['product'],
                            portion=ingr['portion'], weight=ingr['weight']))
          ingr_to_save.append(models.IngrACIndex(key_name=ingr['product'], idx=models.IngrACIndex.make_index(ingr['product'])))
          
        db.put(ingr_to_save)

        # uaktualnij użytkownika
        if recipe.rec_vis == VISIBILITY[2]:
          def utx():
            user = PMMUser.get(self.request.user.key())
            user.rec_pub += 1
            user.put()
            cache_delete('gfcu', self.request.user.key().name())
          db.run_in_transaction(utx)

        # Dodaj podwójny licznik...
        Counter.init_shards(SHARD_RECIPE_KEY % recipe.key(), 2) # 2 means about 15 writes/s per recipe 
        
        # na później odłóż indeksację, uaktualnienie tagów i licznika kategorii
        deferred_lib.defer(deferred.recipe_update, recipe.key(), 'add')

        # wyślij powiadomienie o dodaniu przepisu!
        if recipe.rec_vis != VISIBILITY[0]:
          try:
            create_activity(self.request.user.key().name(),
                            u'%s dodał(a) przepis <a href="%s">%s</a>' % (self.request.user.display_name, recipe.get_url(True), recipe.title),
                            u'Przejrzyj go, oceń lub dodaj do ulubionych.'
            )
          except Exception, e:
            pass
            
        self.request.notifications.success('Przepis dodany!')
        return redirect(recipe.get_url())
      except Exception, e:
        logging.exception('Recipe add failed (%s): ' % self.request.user + str(e))
        self.request.notifications.error('Przepisu nie dodano! Wystąpił błąd zapisu, spróbuj ponownie...')    
    else:
      self.request.notifications.error(u'Przepisu nie dodano! Formularz zawiera błędy.')
    return self.get()


class RecipeEditHandler(LoginRequiredHandler):
  def init(self, key):
    self.recipe = get_or_404(models.Recipe, key)
    if self.recipe.disabled:
      return NotFound()
      
    if not (self.request.user.is_admin or self.request.user.key() == self.recipe.parent_key()):
      return Unauthorized()
    
    self.ingredients = models.RecipeIngr.all().ancestor(self.recipe).order('__key__').fetch(20)
    
    initial = {}
    initial['title'] = self.recipe.title
    initial['recipe'] = self.recipe.recipe
    initial['tags'] = ', '.join(self.recipe.tags)
    initial['category'] = self.recipe.category
    initial['phase'] = self.recipe.phase
    initial['type'] = self.recipe.type
    initial['ig'] = self.recipe.ig
    initial['time'] = self.recipe.time
    initial['rec_vis'] = self.recipe.rec_vis
    initial['ingr'] = [{
      'product': i.product,
      'portion': i.portion,
      'weight': i.weight
      } for i in self.ingredients]
    self.form = RecipeForm(initial, edit=True)
    if self.recipe.rec_vis == VISIBILITY[1]:
      self.form.rec_vis.choices = [VISIBILITY[1], VISIBILITY[2]]
    if self.recipe.rec_vis == VISIBILITY[2]:
      self.form.rec_vis.choices = [VISIBILITY[2]]

  def get(self, key):
    ret = self.init(key)
    if ret:
      return ret

    return render_to_response('przepisy/edit.html', {
      'form': self.form.as_widget(),
    })

  def post(self, key):
    ret = self.init(key)
    if ret:
      return ret

    if self.form.validate(self.request.form):
      if self.form.has_changed:
        try:
          self.recipe.title = self.form['title']
          self.recipe.recipe = self.form['recipe']
          self.recipe.recipe_html = markdown2html(self.form['recipe'])
          self.recipe.phase = self.form['phase']
          self.recipe.type = self.form['type']
          self.recipe.ig = self.form['ig']
          self.recipe.time = int(self.form['time'])
          self.recipe.ingr_count = len(self.form['ingr'])
          
          new_tags = models.Tag.split_elements(self.form['tags'])
          tag_diff = models.Tag.find_differences(self.recipe.tags, new_tags)
          self.recipe.tags = new_tags
        
          if self.recipe.category != self.form['category']:
            category_diff = self.recipe.category, self.form['category']
          else:
            category_diff = ()
          self.recipe.category = self.form['category']
          
          if self.recipe.rec_vis != self.form['rec_vis']:
            rec_vis_diff = self.recipe.rec_vis, self.form['rec_vis']
          else:
            rec_vis_diff = ()
          self.recipe.rec_vis = self.form['rec_vis']
          
          # zapisz dane przepisu
          self.recipe.put()
          
          # usuń nadmiarowe składniki
          if len(self.ingredients) > len(self.form['ingr']):
            db.delete([db.Key.from_path('RecipeIngr', '%2d'%(i+1), parent=self.recipe.key()) for i in range(len(self.form['ingr']), len(self.ingredients))])
          
          # nadpisz istniejące lub dodaj nowe; dodaj AC składników, jeśli nowe
          ingr_to_save = []
          old_ingr_names = [i.product for i in self.ingredients]
          for i, ingr in enumerate(self.form['ingr']):
            ingr_to_save.append(models.RecipeIngr(parent=self.recipe, key_name='%2d'%(i+1), product=ingr['product'],
                              portion=ingr['portion'], weight=ingr['weight']))
            if ingr['product'] not in old_ingr_names:
              ingr_to_save.append(models.IngrACIndex(key_name=ingr['product'], idx=models.IngrACIndex.make_index(ingr['product'])))
          db.put(ingr_to_save)

          # uaktualnij użytkownika
          if rec_vis_diff and self.recipe.rec_vis != VISIBILITY[2]:
            def utx():
              user = PMMUser.get(self.request.user.key())
              user.rec_pub -= 1
              if user.rec_pub < 0:
                user.rec_pub = 0
              user.put()
              cache_delete('gfcu', self.request.user.key().name())
            db.run_in_transaction(utx) 
          elif rec_vis_diff and self.recipe.rec_vis == VISIBILITY[2]:
            def utx():
              user = PMMUser.get(self.request.user.key())
              user.rec_pub += 1
              user.put()
              cache_delete('gfcu', self.request.user.key().name())
            db.run_in_transaction(utx) 
          
          # na później odłóż indeksację, uaktualnienie tagów i licznika kategorii
          deferred_lib.defer(deferred.recipe_update, self.recipe.key(), 'update', tag_diff, category_diff, rec_vis_diff)
  
          # wyślij powiadomienie o dodaniu przepisu!
          if self.recipe.rec_vis != VISIBILITY[0]:
            try:
              create_activity(self.request.user.key().name(),
                              u'%s zmodyfikował(a) przepis <a href="%s">%s</a>' % (self.request.user.display_name, self.recipe.get_url(True), self.recipe.title),
                              u'Zobacz, co się zmieniło.'
              )
            except Exception, e:
              pass
              
          self.request.notifications.success('Zapisano zmodyfikowany przepis!')
          return redirect(self.recipe.get_url())
        except Exception, e:
          logging.exception('Recipe add failed (%s): ' % self.request.user + str(e))
          self.request.notifications.error('Przepisu nie zmieniono! Wystąpił błąd zapisu, spróbuj ponownie...')
      else:
        self.request.notifications.warning('Przepisu nie zmieniono, ponieważ nie wprowadzono żadnych zmian!')
    else:
      self.request.notifications.error(u'Przepisu nie zmieniono! Formularz zawiera błędy.')

    return render_to_response('przepisy/edit.html', {
      'form': self.form.as_widget(),
    })


def index(request):
  return redirect(url_for('przepisy/search'))


def search(request, ordering='popularne'):
  query = request.args.get('q', '').strip()
  page = request.args.get('p', 1, type=int)
  if page < 1:
    page = 1
  order = request.args.get('o', '')
  if order != '' and order not in ORDERINGS.keys():
    order = ''
  exact = request.args.get('e', '1')
  if exact not in ('0', '1'):
    exact = '1'
  advanced = request.args.get('a', '0')
  if advanced not in ('0', '1'):
    advanced = '0'

  recipes = models.Recipe.search(query, 201, order=ORDERINGS[order] if order else None, exact=True if exact == '1' else False)
  is_more = len(recipes) > 200
  if is_more:
    recipes = recipes[:200]
  
  # Przygotuj urle
  if page != 1:
    prev = url_for('przepisy/search', q=query, p=page-1, o=order, e=exact, a=advanced)
  else:
    prev = None
  
  pages = int(math.ceil(len(recipes)/float(settings.PAGE_SIZE)))
  if pages != page and pages > 1:
    next = url_for('przepisy/search', q=query, p=page+1, o=order, e=exact, a=advanced)
  else:
    next = None
  
  # Końcowa lista przepisów, po przycięciu
  if pages > 1:
    recipes = recipes[settings.PAGE_SIZE*(page-1):settings.PAGE_SIZE*page]
  recipes = models.Recipe.get(recipes)
  recipes = [recipe for recipe in recipes if recipe is not None]
  
  # Get authors, TODO: OPTIMIZE
  authors = PMMUser.get([recipe.parent_key() for recipe in recipes])
  for i, recipe in enumerate(recipes):
    if recipe and authors[i]:
      recipe.author = authors[i]
  
  if request.is_xhr:
    return render_to_response('przepisy/includes/search_list.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
    })
  else:
    pop_recipes = models.Recipe.all() \
      .filter('rec_vis =', VISIBILITY[2]) \
      .filter('disabled =', False) \
      .order('-views') \
      .fetch(20)
    
    return render_to_response('przepisy/search.html', {
      'recipes': recipes,
      'prev': prev,
      'order': order,
      'page': page,
      'exact': exact,
      'advanced': advanced,
      'query': query,
      'squery': query,
      'next': next,
      'is_more': is_more,
      'pop_recipes': pop_recipes,
    })


def markdown_preview(request):
  return render_to_response('przepisy/markdown_preview.html', {'recipe': request.form.get('recipe', '')})


@no_session
def autocomplete(request, model):
  q = request.args.get('q', None)  
  try:
    limit = int(request.args.get('limit', '50'))
  except ValueError, e:
    limit = 50
  
  if (model not in ('tag', 'product') or q is None or q == ''):
    return NotFound()
  
  if model == 'tag':
    results = models.TagACIndex.search(q, limit=limit)
  if model == 'product':
    results = models.IngrACIndex.search(q, limit=limit)
    
  if results:
    return Response(u'\n'.join(results))
  else:
    return Response(u'')


def view(request, author, slug):
  recipe = get_or_404(models.Recipe, db.Key.from_path('PMMUser', author, 'Recipe', slug))
  if recipe.disabled:
    return NotFound()

  similar = models.Recipe.search(recipe.title, limit=10, order='-created')
  if recipe.key() in similar:
    similar.remove(recipe.key())
  similar = db.get(similar)

  is_author = False
  if request.user.is_authenticated() and request.user.is_admin:
    is_admin = True
  else:
    is_admin = False
  
  if request.user.is_authenticated() and author == request.user.key().name():
    show = True
    is_author = True
  elif recipe.rec_vis == VISIBILITY[0] and (request.user.is_anonymous() or author != request.user.key().name()):
    show = False  
  elif recipe.rec_vis == VISIBILITY[1] and (request.user.is_anonymous() or not is_my_friend(request.user.key().name(), author)):
    show = False
  else:
    show = True
  
  if show:
    ingredients = models.RecipeIngr.all().ancestor(recipe).order('__key__').fetch(20)
    
    if request.user.is_authenticated():
      is_a_fave = models.Favs.is_a_fave(request.user.key(), recipe.key())
    else:
      is_a_fave = False
      
    return render_to_response('przepisy/view.html', {
      'recipe': recipe,
      'ingredients': ingredients,
      'similar': similar,
      'is_a_fave': is_a_fave,
      'is_author': is_author,
      'is_admin': is_admin,
    })
  else:
    return render_to_response('przepisy/view_private.html', {
      'recipe': recipe,
      'similar': similar,
      'private': recipe.rec_vis == VISIBILITY[0],
      'is_admin': is_admin,
    })


@no_cache
@no_session
def count_view(request, key):
  try:
    db_key = db.Key(key)
    
    if db_key.kind() == 'Recipe':
      shard_key = SHARD_RECIPE_KEY % key
    else:
      shard_key = None
    
    if shard_key:
      Counter.incr(shard_key)

  except: # Don't care that much if something got wrong
    logging.exception('Error in count view')
    pass
  
  response = Response('GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', mimetype='image/gif')
  response.expires = datetime.datetime(2009, 1, 1)
  response.cache_control.must_revalidate = True
  
  return response


@no_cache
def update_recipe_views(request):
  recalculate_views()
  return Response('OK')


@no_cache
def update_friends_views(request):
  update_friends()
  return Response('OK')


def favs_button(request, operation, key):
  if operation not in ('dodaj', 'usun'):
    return NotFound()
    
  if request.user.is_anonymous():
    return Unauthorized()
  
  db_key = db.Key(key)
    
  if db_key.kind() != 'Recipe':
    return NotFound()
    
  if operation == 'dodaj':
    models.Favs.add_one(request.user.key(), db_key)
    return render_json_response({'msg': 'Przepis dodany do ulubionych'})
  else:
    models.Favs.remove_one(request.user.key(), db_key)
    return render_json_response({'msg': 'Przepis usunięty z ulubionych'})


@login_required
def my_list(request, ordering='popularne'):
  if ordering not in ORDERINGS.keys():
    return NotFound()
  
  prev, recipes, next = PagerQuery(models.Recipe) \
    .ancestor(request.user) \
    .filter('disabled =', False) \
    .order(ORDERINGS[ordering]) \
    .fetch(settings.PAGE_SIZE, request.args.get('b', None))
  
  if request.is_xhr:
    return render_to_response('przepisy/includes/my_list.html', {
      'recipes': recipes,
      'prev': prev,
      'ordering': ordering,
      'next': next,
    })
  else:
    return render_to_response('przepisy/my_list.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
      'ordering': ordering,
      'fav_recipes': models.Favs.get_list(request.user.key()),
    })


@admin_required
def disabled_list(request):  
  prev, recipes, next = PagerQuery(models.Recipe) \
    .filter('disabled =', True) \
    .order('-updated') \
    .fetch(settings.PAGE_SIZE, request.args.get('b', None))

  # Get authors, TODO: OPTIMIZE
  authors = PMMUser.get([recipe.parent_key() for recipe in recipes])
  for i, recipe in enumerate(recipes):
    if recipe and authors[i]:
      recipe.author = authors[i]

  if request.is_xhr:
    return render_to_response('przepisy/includes/disabled_list.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
    })
  else:
    return render_to_response('przepisy/disabled_list.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
    })


def list(request, ordering='popularne'):
  if ordering not in ORDERINGS.keys():
    return NotFound()
  
  prev, recipes, next = PagerQuery(models.Recipe) \
    .filter('rec_vis =', VISIBILITY[2]) \
    .filter('disabled =', False) \
    .order(ORDERINGS[ordering]) \
    .fetch(settings.PAGE_SIZE, request.args.get('b', None))
  
  # Get authors, TODO: OPTIMIZE
  authors = PMMUser.get([recipe.parent_key() for recipe in recipes])
  for i, recipe in enumerate(recipes):
    if recipe and authors[i]:
      recipe.author = authors[i]
  
  if request.is_xhr:
    template = 'przepisy/includes/list.html'
  else:
    template = 'przepisy/list.html'
  
  return render_to_response(template, {
    'recipes': recipes,
    'prev': prev,
    'ordering': ordering,
    'next': next,
  })


def remove(request, key):
  if request.method != 'POST':
    return MethodNotAllowed()
  
  if request.user.is_anonymous():
    return Unauthorized()
    
  recipe = models.Recipe.get(key)
  if not recipe:
    return NotFound()
  
  # Użytkownik może usunąć swój publiczny przepis tą metodą, ale nie jest to reklamowane!
  if not (request.user.is_admin or request.user.key() == recipe.parent_key()):
    return Unauthorized()
  
  # Jeśli jest już wyłączony, wykonaj prostsze kroki usuwające
  if recipe.disabled:
    to_delete = models.RecipeIngr.all().ancestor(recipe).fetch(20)
    db.delete(to_delete)
  
    Counter.remove_by_name(SHARD_RECIPE_KEY % recipe.key())
    
    recipe.delete()
  else:
    # Zmień status na wyłączony  
    recipe.disabled = True
    recipe.put()
    
    # Usuń liczniki, składniki i użytkownika
    to_delete = models.RecipeIngr.all().ancestor(recipe).fetch(20)
    db.delete(to_delete)
    
    Counter.remove_by_name(SHARD_RECIPE_KEY % recipe.key())
    
    if recipe.rec_vis == VISIBILITY[2]:
      def utx():
        user = PMMUser.get(recipe.parent_key())
        user.rec_pub -= 1
        if user.rec_pub < 0:
          user.rec_pub = 0
        user.put()
        cache_delete('gfcu', recipe.parent_key().name())
      db.run_in_transaction(utx)
  
    # na później odłóż indeksację, uaktualnienie tagów i licznika kategorii
    deferred_lib.defer(deferred.recipe_update, recipe.key(), 'delete')
  
  request.notifications.success('Przepis usunięty!')
  return render_json_response({'redirectUrl': url_for('przepisy/my_list')})


def disable(request, key):   
  if request.method != 'POST':
    return MethodNotAllowed()

  if request.user.is_anonymous() or not request.user.is_admin:
    return Unauthorized()
    
  recipe = models.Recipe.get(key)
  if not recipe:
    return NotFound()
  
  # Zmień status na wyłączony
  recipe.disabled = True
  recipe.put()  

  if recipe.rec_vis == VISIBILITY[2]:
    def utx():
      user = PMMUser.get(recipe.parent_key())
      user.rec_pub -= 1
      if user.rec_pub < 0:
        user.rec_pub = 0
      user.put()
      cache_delete('gfcu', recipe.parent_key().name())
    db.run_in_transaction(utx)

  # na później odłóż indeksację, uaktualnienie tagów i licznika kategorii
  deferred_lib.defer(deferred.recipe_update, recipe.key(), 'disable')

  request.notifications.success('Przepis wyłączony!')
  return render_json_response({'redirectUrl': url_for('przepisy/disabled_list')})


def enable(request, key):   
  if request.method != 'POST':
    return MethodNotAllowed()

  if request.user.is_anonymous() or not request.user.is_admin:
    return Unauthorized()
    
  recipe = models.Recipe.get(key)
  if not recipe:
    return NotFound()
  
  # Zmień status na włączony
  recipe.disabled = False
  recipe.put()

  if recipe.rec_vis == VISIBILITY[2]:
    def utx():
      user = PMMUser.get(recipe.parent_key())
      user.rec_pub += 1
      user.put()
      cache_delete('gfcu', recipe.parent_key().name())
    db.run_in_transaction(utx)

  # na później odłóż indeksację, uaktualnienie tagów i licznika kategorii
  deferred_lib.defer(deferred.recipe_update, recipe.key(), 'enable')

  request.notifications.success('Przepis włączony!')
  return render_json_response({'redirectUrl': url_for('przepisy/disabled_list')})


def atom_feed(request):
  feed = AtomFeed(u"Najnowsze przepisy diety Montignac", feed_url=request.url,
                  url=request.host_url,
                  subtitle=u"Lista 20 najnowszych przepisów publicznych dodanych przez użytkowników witryny.")

  recipes = models.Recipe.all().filter('rec_vis =', VISIBILITY[2]).filter('disabled =', False).order('-created').fetch(20)

  # Get authors, TODO: OPTIMIZE
  authors = PMMUser.get([recipe.parent_key() for recipe in recipes])
  for i, recipe in enumerate(recipes):
    if recipe and authors[i]:
      recipe.author = authors[i]
    else:
      recipe.author = 'Nieznany'

  for post in recipes:
    body = post.recipe_html + u'<p><i>Proporcje składników znajdziesz na witrynie...</i></p>'
    feed.add(post.title, body, content_type='html',
            author=post.author, url=post.get_url(True), category=post.category,
            updated=post.updated, published=post.created)
  return feed.get_response()


def category(request, slug, ordering='popularne'):
  if slug in models.CATEGORIES_SV.keys():
    category = get_by_key_name_or_404(models.Category, models.CATEGORIES_SV[slug])
  else:
    return NotFound()
  
  if ordering not in ORDERINGS.keys():
    return NotFound()
  
  if category.counter == 0:
    prev, recipes, next = None, [], None
  else:
    prev, recipes, next = PagerQuery(models.Recipe) \
      .filter('rec_vis =', VISIBILITY[2]) \
      .filter('disabled =', False) \
      .filter('category =', slug) \
      .order(ORDERINGS[ordering]) \
      .fetch(settings.PAGE_SIZE, request.args.get('b', None))
  
    # Get authors, TODO: OPTIMIZE
    authors = PMMUser.get([recipe.parent_key() for recipe in recipes])
    for i, recipe in enumerate(recipes):
      if recipe and authors[i]:
        recipe.author = authors[i]
  
  if request.is_xhr:
    return render_to_response('przepisy/includes/category_list.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
      'ordering': ordering,
      'category_slug': slug
    })
  else:
    categories = [c for c in models.Category.get_for_lists() if c['name'] != category.key().name()]
    return render_to_response('przepisy/category.html', {
      'recipes': recipes,
      'prev': prev,
      'next': next,
      'ordering': ordering,
      'category_slug': slug,
      'category': category.key().name(),
      'categories': categories,
    })


@login_required
def friend_list(request, ordering='popularne'):
  if ordering not in ORDERINGS.keys():
    return NotFound()
  
  friends = get_cached_friends(request.user.key().name())
  
  if friends:
    prev, recipes, next = PagerQuery(models.RecipeFriends) \
      .filter('friends =', request.user.key().name()) \
      .order(ORDERINGS[ordering]) \
      .fetch(settings.PAGE_SIZE, request.args.get('b', None))
    
    recipes = models.Recipe.get([recipe.parent_key() for recipe in recipes])
  
    # Get authors, TODO: OPTIMIZE
    authors = PMMUser.get([recipe.parent_key() for recipe in recipes])
    for i, recipe in enumerate(recipes):
      if recipe and authors[i]:
        recipe.author = authors[i]
  else:
    prev, recipes, next = None, [], None
      
  
  if request.is_xhr:
    template = 'przepisy/includes/friend_list.html'
  else:
    template = 'przepisy/friend_list.html'
  
  return render_to_response(template, {
    'recipes': recipes,
    'prev': prev,
    'ordering': ordering,
    'next': next,
    'friends': friends.values(),
  })
  