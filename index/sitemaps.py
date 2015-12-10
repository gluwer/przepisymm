from kay.utils import url_for

from kay_sitemap import Sitemap

from przepisy import VISIBILITY
from przepisy.models import Category, Recipe


class StaticSitemap(Sitemap):
  changefreq = 'weekly'
  
  def items(self):
    items = [url_for('index/index', _external=True)]
    for cat in Category.all().fetch(20):
      items.append(cat.get_url(True))
    return items
  
  
class RecipesSitemap(Sitemap):
  changefreq = 'weekly'
  
  def items(self):
    return Recipe.all().filter('rec_vis =', VISIBILITY[2]).filter('disabled =', False).order('-created').fetch(200)

  def lastmod(self, item):
    return item.updated
