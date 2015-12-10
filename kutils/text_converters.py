# coding: utf-8

from jinja2 import environmentfilter, Markup
from kay.conf import settings

def markdown2html(text):
  """Transform markdown text to HTML using settings.MARKDOWN options dict."""
  import markdown
  
  md = markdown.Markdown(**getattr(settings, 'MARKDOWN', {}))
  return md.convert(text)


@environmentfilter
def markdown_filter(environment, value):
  result = markdown2html(value)
  
  if environment.autoescape:
    result = Markup(result)
  return result 