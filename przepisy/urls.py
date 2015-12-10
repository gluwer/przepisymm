# -*- coding: utf-8 -*-
# przepisy.urls


from werkzeug.routing import (
  Map, Rule, Submount,
  EndpointPrefix, RuleTemplate,
)

def make_rules():
  return [
    EndpointPrefix('przepisy/', [
      Rule('/', endpoint='index'),
      Rule('/feed/atom', endpoint='atom_feed'),
      Rule('/szukaj', endpoint='search'),
      Rule('/kategoria/<slug>', defaults={'ordering': 'popularne'}, endpoint='category'),
      Rule('/kategoria/<slug>/<ordering>', endpoint='category'),
      Rule('/autocomplete/<model>', endpoint='autocomplete'),
      Rule('/p/<author>/<slug>', endpoint='recipe'),
      Rule('/moje', defaults={'ordering': 'popularne'}, endpoint='my_list'),
      Rule('/moje/<ordering>', endpoint='my_list'),
      Rule('/znajomych', defaults={'ordering': 'popularne'}, endpoint='friend_list'),
      Rule('/znajomych/<ordering>', endpoint='friend_list'),
      Rule('/lista', defaults={'ordering': 'popularne'}, endpoint='list'),
      Rule('/lista/<ordering>', endpoint='list'),
      Rule('/dodaj', endpoint='add'),
      Rule('/edytuj/<key>', endpoint='edit'),
      Rule('/usun/<key>', endpoint='remove'),
      Rule('/zablokuj/<key>', endpoint='disable'),
      Rule('/odblokuj/<key>', endpoint='enable'),
      Rule('/wylaczone', endpoint='disabled_list'),
      Rule('/podglad', endpoint='markdown_preview'),
      Rule('/stat/<key>', endpoint='count_view'),
      Rule('/ulubione/<operation>/<key>', endpoint='favs_button'),
      Rule('/cron/update_recipe_views', endpoint='update_recipe_views'),
      Rule('/cron/update_friends', endpoint='update_friends_views'),
    ]),
  ]

all_views = {
  'przepisy/index': 'przepisy.views.index',
  'przepisy/category': 'przepisy.views.category',
  'przepisy/add': ('przepisy.views.RecipeAddHandler',(), {}),
  'przepisy/autocomplete': 'przepisy.views.autocomplete',
  'przepisy/markdown_preview': 'przepisy.views.markdown_preview',
  'przepisy/recipe': 'przepisy.views.view',
  'przepisy/update_recipe_views': 'przepisy.views.update_recipe_views',
  'przepisy/count_view': 'przepisy.views.count_view',
  'przepisy/edit': ('przepisy.views.RecipeEditHandler',(), {}),
  'przepisy/remove': 'przepisy.views.remove',
  'przepisy/disable': 'przepisy.views.disable',
  'przepisy/favs_button': 'przepisy.views.favs_button',
  'przepisy/my_list': 'przepisy.views.my_list',
  'przepisy/list': 'przepisy.views.list',
  'przepisy/enable': 'przepisy.views.enable',
  'przepisy/disabled_list': 'przepisy.views.disabled_list',
  'przepisy/search': 'przepisy.views.search',
  'przepisy/atom_feed': 'przepisy.views.atom_feed',
  'przepisy/friend_list': 'przepisy.views.friend_list',
  'przepisy/update_friends_views': 'przepisy.views.update_friends_views',
}
