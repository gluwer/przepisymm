#!/usr/bin/python
import os
import shutil
import urllib
import clevercss

COMPRESS = True

IN_PATH_JS = os.path.join('js')
OUT_PATH_JS = os.path.join('..','m')
JS_FILES = {
    'a.js': {
        'comment': 'Copyright (c) 2009-2010 Rafal Jonca; Includes also several jQuery plugins.',
        'files':('jquery-geturlparam.js', 'jquery-numeric.js', 'jquery-autocomplete.js', 'lib.js', 'recipe.js', 'main.js',)
    }
}

IN_PATH_CSS = os.path.join('css')
OUT_PATH_CSS = os.path.join('..','m')
CSS_FILES = {
    'a.css': {
        'comment': 'Copyright (c) 2009-2010 Rafal Jonca; contains YUI3 CSS (http://developer.yahoo.net/yui/license.txt)',
        'files':('yui3.css', 'helpers.css', 'sprites-sprite.css', 'style.ccss')
    }
}

"""
CLEVERCSS_CONTEXT = { # Fiolet
  'sbox_width': '300px',
  'main_color': '#636',
  'main_color_light': '#969'
}

CLEVERCSS_CONTEXT = { # Indigo
  'sbox_width': '300px',
  'main_color': '#336',
  'main_color_light': '#669'
}
"""

CLEVERCSS_CONTEXT = { # Niebieski
  'sbox_width': '300px',
  'main_color': '#2B6488',
  'main_color_light': '#3C91C7'
}

IN_PATH_COPY = os.path.join('css', 'i')
OUT_PATH_COPY = os.path.join('..','m', 'i')
COPY_FILES = ('icons.png',)

# Simple Class for CSS code compression with 3 levels of compressability:
# SIMPLE (only longer comments and empty lines),
# NORMAL (SIMPLE + one line per rule, cut unnecessary spaces and chars),
# FULL (all comments, all CSS in one line).
#
# You can use shorthand function minimalize() to compress without manual instantiation.
#
# Author: Rafal Jonca

import re

# Constants for use in compression level setting.
NONE = 0
SIMPLE = 1
NORMAL = 2
FULL = 3

_REPLACERS = {
    NONE: (None),                           # dummy
    SIMPLE: ((r'\/\*.{4,}?\*\/', ''),       # comment
             (r'\n\s*\n', r"\n"),           # empty new lines
             (r'(^\s*\n)|(\s*\n$)', "")),   # new lines at start or end
    NORMAL: ((r'/\*.{4,}?\*/', ''),         # comments
             (r"\n", ""),                   # delete new lines
             ('[\t ]+', " "),               # change spaces and tabs to one space
             (r'\s?([;:{},+>])\s?', r"\1"), # delete space where it is not needed, change ;} to }
             (r';}', "}"),                  # because semicolon is not needed there
             (r'}', r"}\n")),               # add new line after each rule
    FULL: ((r'\/\*.*?\*\/', ''),            # comments
           (r"\n", ""),                     # delete new lines
           (r'[\t ]+', " "),                # change spaces and tabs to one space
           (r'\s?([;:{},+>])\s?', r"\1"),   # delete space where it is not needed, change ;} to }
           (r';}', "}")),                   # because semicolon is not needed there
}

class CssMin:
    def __init__(self, level=NORMAL):
        self.level = level

    def compress(self, css):
        """Tries to minimize the length of CSS code passed as parameter. Returns string."""
        css = css.replace("\r\n", "\n") # get rid of Windows line endings, if they exist
        for rule in _REPLACERS[self.level]:
            css = re.compile(rule[0], re.MULTILINE|re.UNICODE|re.DOTALL).sub(rule[1], css)
        return css

def minimalize(css, level=NORMAL):
    """Compress css using level method and return new css as a string."""
    return CssMin(level).compress(css)


# This code is original from jsmin by Douglas Crockford, it was translated to
# Python by Baruch Even. The original code had the following copyright and
# license.
#
# /* jsmin.c
#    2007-05-22
#
# Copyright (c) 2002 Douglas Crockford  (www.crockford.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# The Software shall be used for Good, not Evil.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# */

from cStringIO import StringIO

def jsmin(js):
    ins = StringIO(js)
    outs = StringIO()
    JavascriptMinify().minify(ins, outs)
    str = outs.getvalue()
    if len(str) > 0 and str[0] == '\n':
        str = str[1:]
    return str

def isAlphanum(c):
    """return true if the character is a letter, digit, underscore,
           dollar sign, or non-ASCII character.
    """
    return ((c >= 'a' and c <= 'z') or (c >= '0' and c <= '9') or
            (c >= 'A' and c <= 'Z') or c == '_' or c == '$' or c == '\\' or (c is not None and ord(c) > 126));

class UnterminatedComment(Exception):
    pass

class UnterminatedStringLiteral(Exception):
    pass

class UnterminatedRegularExpression(Exception):
    pass

class JavascriptMinify(object):

    def _outA(self):
        self.outstream.write(self.theA)
    def _outB(self):
        self.outstream.write(self.theB)

    def _get(self):
        """return the next character from stdin. Watch out for lookahead. If
           the character is a control character, translate it to a space or
           linefeed.
        """
        c = self.theLookahead
        self.theLookahead = None
        if c == None:
            c = self.instream.read(1)
        if c >= ' ' or c == '\n':
            return c
        if c == '': # EOF
            return '\000'
        if c == '\r':
            return '\n'
        return ' '

    def _peek(self):
        self.theLookahead = self._get()
        return self.theLookahead

    def _next(self):
        """get the next character, excluding comments. peek() is used to see
           if a '/' is followed by a '/' or '*'.
        """
        c = self._get()
        if c == '/':
            p = self._peek()
            if p == '/':
                c = self._get()
                while c > '\n':
                    c = self._get()
                return c
            if p == '*':
                c = self._get()
                while 1:
                    c = self._get()
                    if c == '*':
                        if self._peek() == '/':
                            self._get()
                            return ' '
                    if c == '\000':
                        raise UnterminatedComment()

        return c

    def _action(self, action):
        """do something! What you do is determined by the argument:
           1   Output A. Copy B to A. Get the next B.
           2   Copy B to A. Get the next B. (Delete A).
           3   Get the next B. (Delete B).
           action treats a string as a single character. Wow!
           action recognizes a regular expression if it is preceded by ( or , or =.
        """
        if action <= 1:
            self._outA()

        if action <= 2:
            self.theA = self.theB
            if self.theA == "'" or self.theA == '"':
                while 1:
                    self._outA()
                    self.theA = self._get()
                    if self.theA == self.theB:
                        break
                    if self.theA <= '\n':
                        raise UnterminatedStringLiteral()
                    if self.theA == '\\':
                        self._outA()
                        self.theA = self._get()


        if action <= 3:
            self.theB = self._next()
            if self.theB == '/' and (self.theA == '(' or self.theA == ',' or
                                     self.theA == '=' or self.theA == ':' or
                                     self.theA == '[' or self.theA == '?' or
                                     self.theA == '!' or self.theA == '&' or
                                     self.theA == '|' or self.theA == ';' or
                                     self.theA == '{' or self.theA == '}' or
                                     self.theA == '\n'):
                self._outA()
                self._outB()
                while 1:
                    self.theA = self._get()
                    if self.theA == '/':
                        break
                    elif self.theA == '\\':
                        self._outA()
                        self.theA = self._get()
                    elif self.theA <= '\n':
                        raise UnterminatedRegularExpression()
                    self._outA()
                self.theB = self._next()


    def _jsmin(self):
        """Copy the input to the output, deleting the characters which are
           insignificant to JavaScript. Comments will be removed. Tabs will be
           replaced with spaces. Carriage returns will be replaced with linefeeds.
           Most spaces and linefeeds will be removed.
        """
        self.theA = '\n'
        self._action(3)

        while self.theA != '\000':
            if self.theA == ' ':
                if isAlphanum(self.theB):
                    self._action(1)
                else:
                    self._action(2)
            elif self.theA == '\n':
                if self.theB in ['{', '[', '(', '+', '-']:
                    self._action(1)
                elif self.theB == ' ':
                    self._action(3)
                else:
                    if isAlphanum(self.theB):
                        self._action(1)
                    else:
                        self._action(2)
            else:
                if self.theB == ' ':
                    if isAlphanum(self.theA):
                        self._action(1)
                    else:
                        self._action(3)
                elif self.theB == '\n':
                    if self.theA in ['}', ']', ')', '+', '-', '"', '\'']:
                        self._action(1)
                    else:
                        if isAlphanum(self.theA):
                            self._action(1)
                        else:
                            self._action(3)
                else:
                    self._action(1)

    def minify(self, instream, outstream):
        self.instream = instream
        self.outstream = outstream
        self.theA = '\n'
        self.theB = None
        self.theLookahead = None

        self._jsmin()
        self.instream.close()


def _do_js():
    for out_file, in_files in JS_FILES.iteritems():
        code = []
        for in_file in in_files['files']:
            f = open(os.path.join(IN_PATH_JS, in_file))
            code.append('/* %s */\n\n' % (in_file))
            code.append(f.read())
            code.append('\n\n')
            f.close()
        code = ''.join(code)
        if COMPRESS:
            code = jsmin(code)
        code = ('/* %s */\n\n' % in_files['comment']) + code
        f = open(os.path.join(OUT_PATH_JS, out_file), 'w')
        f.write(code)
        f.close()

def _do_css():
    for out_file, in_files in CSS_FILES.iteritems():
        code = []
        for in_file in in_files['files']:
            f = open(os.path.join(IN_PATH_CSS, in_file))
            code.append('/* %s */\n\n' % (in_file))
            if in_file.endswith('ccss'):
                code.append(clevercss.convert(f.read(), CLEVERCSS_CONTEXT))
            else:
                code.append(f.read())
            code.append('\n\n')
            f.close()
        code = ''.join(code)
        if COMPRESS:
            code = minimalize(code, level=FULL)
        code = ('/* %s */\n\n' % in_files['comment']) + code
        f = open(os.path.join(OUT_PATH_CSS, out_file), 'w')
        f.write(code)
        f.close()

def _do_copy():
    for file in COPY_FILES:
        in_file, out_file = os.path.join(IN_PATH_COPY, file), os.path.join(OUT_PATH_COPY, file)
        try:
          os.remove(out_file)
        except:
          pass
        shutil.copyfile(in_file, out_file)

if __name__ == '__main__':
    _do_js()
    _do_css()
    _do_copy()
