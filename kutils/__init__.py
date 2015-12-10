# coding: utf-8

POLISH_REPLACE = {
  u'ą': 'a', 
  u'ć': 'c',
  u'ę': 'e',
  u'ł': 'l',
  u'ś': 's',
  u'ż': 'z',
  u'ź': 'z',
  u'ń': 'n',
  u'ó': 'o',
  u'Ą': 'A', 
  u'Ć': 'C',
  u'Ę': 'E',
  u'Ł': 'L',
  u'Ś': 'S',
  u'Ż': 'Z',
  u'Ź': 'Z',
  u'Ń': 'N',
  u'Ó': 'O',
}

def slugify(value):
  """Converts value to url safe one."""
  import unicodedata, re
  for c, r in POLISH_REPLACE.iteritems():
    value = value.replace(c, r)
  value = unicodedata.normalize('NFKD', value ).encode('ascii', 'ignore')
  value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
  return re.sub('[-\s]+', '-', value)