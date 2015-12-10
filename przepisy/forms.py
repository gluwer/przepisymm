# coding: utf-8
from google.appengine.ext import db

from kay.utils import forms, get_request, validators

from kutils import slugify

from przepisy import *
from przepisy import models


class RecipeForm(forms.Form):
  title = forms.TextField(required=True, label=u'Nazwa', max_length=60, min_length=4,
                          help_text=u'Nazwa przepisu powinna być możliwie jednoznaczna.')
  ingr = forms.Multiple(forms.Mapping(
      product=forms.TextField(required=True, label=u'Produkt', max_length=50, min_length=3),
      portion=forms.FloatField(required=True, label=u'Porcja', min_value=0.0, max_value=10000.0),
      weight=forms.ChoiceField(required=True, choices=PORTION_WEIGHTS, label=u'')
    ),
    required=False, label=u'Składniki', min_size=1, max_size=21,
    help_text=u'Wprowadź nazwy i ilość <b>wymaganych</b> składników. Opcjonalne składniki podaj w sposobie przyrządzenia. W miarę możliwości podawaj wartość w gramach!'
  )
  recipe = forms.TextField(required=True, label=u'Sposób przyrządzenia', min_length=10, max_length=2000,
                          help_text=u'Opisz, najlepiej w punktach, sposób przyrządzenia dania.',
                          widget=forms.Textarea)

  tags = forms.TextField(label=u'Etykiety', max_length=50, required=False,
                          help_text=u'Dodaj etykiety (np. dla dzieci, przyjęcia) ułatwiające odnalezienie przepisu w przyszłości. Staraj się nie stosować określeń dotyczących jego nazwy, składników, kategorii, fazy itp. ')
  category = forms.ChoiceField(required=True, choices=CATEGORIES, label=u'Kategoria')
  phase = forms.ChoiceField(required=True, choices=PHASES, label=u'Faza', widget=forms.RadioButtonGroup)
  type = forms.ChoiceField(required=True, choices=TYPES, label=u'Typ', widget=forms.RadioButtonGroup)
  time = forms.ChoiceField(required=True, choices=TIMES, label=u'Czas przygotowania')
  ig = forms.IntegerField(min_value=0, max_value=200, label=u'Przewidywany IG',
                          help_text=u'Jeśli nie potrafisz określić prawdopodobnego IG gotowego dania, pozostaw pole pustym.')
  rec_vis = forms.ChoiceField(default=True, label=u'Widoczny dla',
                              widget=forms.RadioButtonGroup, choices=VISIBILITY,
                              help_text=u'Określ widoczność przepisu dla innych. Tylko <b>publiczne</b> przepisy można wyszukiwać poleceniem szukaj!')

  def __init__(self, initial=None, edit=False):
    self.edit = edit
    super(RecipeForm, self).__init__(initial)

  def validate_title(self, value):
    if self.edit:
      return
    
    slug = slugify(value)
    obj = db.get(db.Key.from_path('Recipe', slug, parent=get_request().user.key()))
    
    if obj:
      raise validators.ValidationError(u"Masz już przepis o zbliżonej nazwie. Użyj innej.")

  def validate_tags(self, value):
    splited = models.Tag.split_elements(value)
    for s in splited:
      if len(s) < 3:
        raise validators.ValidationError(u"Wszystkie etykiety muszą mieć przynajmniej trzy znaki.")
        
    if len(splited) != len(set(splited)):
      raise validators.ValidationError(u"Etykiety nie mogą się powtarzać.")
