# coding: utf-8
from werkzeug import redirect

from kay.handlers import BaseHandler
from kay.utils import create_login_url


class LoginRequiredHandler(BaseHandler):
  """A baseclass for login required view."""

  def __call__(self, request, **kwargs):
    if request.user.is_anonymous():
      return redirect(create_login_url(request.url))
    return super(LoginRequiredHandler, self).__call__(request, **kwargs)

