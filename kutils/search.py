# coding: utf-8
# Parts of this code come from http://bitbucket.org/IanLewis/misopotato

import re
import string

DELIMETER_REGEXP = re.compile('[' + re.escape(string.punctuation) + ']')

FULL_TEXT_STOP_WORDS = frozenset([u'a', u'aby', u'ale', u'bardziej', u'bardzo', u'bez', u'bo',
                                   u'bowiem', u'być', u'była', u'było', u'były', u'będzie', u'co',
                                   u'czy', u'czyli', u'dla', u'dlatego', u'do', u'gdy', u'gdzie',
                                   u'go', u'i', u'ich', u'im', u'innych', u'iż', u'jak', u'jako', u'jednak',
                                   u'jego', u'jej', u'jest', u'jeszcze', u'jeśli', u'już', u'kiedy', u'kilka',
                                   u'która', u'które', u'którego', u'której', u'który', u'których', u'którym',
                                   u'którzy', u'lub', u'ma', u'mi', u'między', u'mnie', u'mogę', u'może', u'można',
                                   u'na', u'nad', u'nam', u'nas', u'naszego', u'naszych', u'nawet', u'nich', u'nie',
                                   u'nim', u'niż', u'o', u'od', u'oraz', u'po', u'pod', u'poza', u'przed', u'przede',
                                   u'przez', u'przy', u'również', u'się', u'sobie', u'swoje', u'są', u'ta', u'tak',
                                   u'takie', u'także', u'tam', u'te', u'tego', u'tej', u'ten', u'też', u'to', u'tu',
                                   u'tych', u'tylko', u'tym', u'u', u'w', u'we', u'wiele', u'wielu', u'więc', u'wszystkich',
                                   u'wszystkim', u'wszystko', u'właśnie', u'z', u'za', u'zawsze', u'ze', u'że',
                                   u'mój', u'moja', u'moje'])

class PolishWordSegmenter(object):
  _FULL_TEXT_MIN_LENGTH = 2

  def __init__(self, word_delimiter_regex=None):
    if word_delimiter_regex is None:
      self._word_delimiter_regex = DELIMETER_REGEXP
    else:
      self._word_delimiter_regex = word_delimiter_regex

  def segment(self, text, remove_stop_words=True):
    if text:
      words = self._word_delimiter_regex.sub(' ', text).lower().split()
      words = set(unicode(w) for w in words)
      if remove_stop_words:
        words -= FULL_TEXT_STOP_WORDS

      for word in list(words):
        if len(word) < self._FULL_TEXT_MIN_LENGTH:
          words.remove(word)

    else:
      words = set()
    return words
  
polish_word_segmenter = PolishWordSegmenter()
