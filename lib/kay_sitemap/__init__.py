class Sitemap(object):
  def __get(self, name, obj, default=None):
    try:
      attr = getattr(self, name)
    except AttributeError:
      return default
    if callable(attr):
      return attr(obj)
    return attr

  def items(self):
    return []

  def location(self, obj):
    if isinstance(obj, basestring):
      return obj
    return obj.get_url(True)

  def get_urls(self):
    urls = []
    for item in self.items():
      lastmod = self.__get('lastmod', item, None)
      if lastmod:
        lastmod = lastmod.strftime('%Y-%m-%d')
      url_info = {
        'location':   self.__get('location', item),
        'lastmod':    lastmod,
        'changefreq': self.__get('changefreq', item, None),
        'priority':   self.__get('priority', item, None)
      }
      urls.append(url_info)
    return urls
