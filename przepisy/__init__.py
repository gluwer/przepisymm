# -*- coding: utf-8 -*-

CATEGORIES = (
  (u'dania-miesne', u'Dania mięsne'),
  (u'dania-rybne', u'Dania rybne'),
  (u'dania-wegetarianskie', u'Dania wegetariańskie'),
  (u'inne', u'Inne'),
  (u'kolacje', u'Kolacje'),
  (u'przekaski', u'Przekąski'),
  (u'salatki-surowki', u'Sałatki i surówki'),
  (u'sniadania', u'Śniadania'),
  (u'wypieki', u'Wypieki'),
  (u'zupy', u'Zupy'),
)
CATEGORIES_SV = dict(CATEGORIES)
CATEGORIES_VS = dict(((v, k) for k, v in CATEGORIES))

PHASES = (u'Faza I i II' ,u'Faza II', u'Odstępstwo')

TYPES = (u'Tłuszczowy', u'Węglowodanowy', u'Mieszany')

TIMES = (
  (u'15',u'Do 15 min.'),
  (u'30',u'Do pół godziny'),
  (u'60',u'Do godziny'),
  (u'90',u'Do półtorej godziny'),
  (u'120',u'Do dwóch godzin'),
  (u'240',u'Ponad dwie godziny'),
)
TIMES_KEYS = (15, 30, 60, 90, 120, 240)
TIMES_SV = dict(TIMES)

PORTION_WEIGHTS = (u'g', u'kg', u'ml', u'l', u'sztuka', u'łyżeczka płaska', u'łyż. stołowa płaska', u'szklanka', u'szczypta', u'kropla')

VISIBILITY = (u'Mnie', u'Znajomych', u'Wszystkich')

SHARD_RECIPE_KEY = 'recipe|%s'

ORDERINGS = {
  'nowe': '-created',
  'popularne': '-views',
  'tytul': 'title',
}
