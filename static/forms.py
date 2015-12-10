# coding: utf-8
from kay.utils.forms import modelform

from static.models import SPage

class SPageForm(modelform.ModelForm):
  class Meta:
    model = SPage
    fields = ('title', 'meta_desc', 'body')
