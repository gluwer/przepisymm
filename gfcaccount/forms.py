# coding: utf-8
from kay.utils.forms import modelform

from gfcaccount.models import PMMUser

class AccountEditForm(modelform.ModelForm):
  class Meta:
    model = PMMUser
    fields = ('rec_vis','pro_vis')
    help_texts = {
      'rec_vis': u'Określa, czy przepisy powinny być <b>domyślnie</b> dostępne tylko dla znajomych, całkowicie publiczne lub tylko prywatne.',
      'pro_vis': u'Określa, czy profil publiczny powinien być dostępny dla wszystkich, tylko znajomych lub ma pozostać ukryty.',
    }
