# Copyright (C) 2013 Paul Weaver <p.weaver@ruthorn.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

from unittest import TestCase

from jcn.formatting import (
    FormatPlaceholderFactory, StringComponent, StringWithFormatting,
    null_placeholder)
from jcn.textwrap import wrap


class TestTextWrapper(TestCase):
    def setUp(self):
        self.format = FormatPlaceholderFactory()

    def test_wrap_str(self):
        text = 'The  quick brown fox jumps over the lazy dog'
        result = wrap(text, width=15)
        expected = [
            'The  quick',
            'brown fox jumps',
            'over the lazy',
            'dog']
        self.assertEqual(result, expected)
        self.assertEqual(wrap('', 10), [])

    def test_wrap_str_with_formatting(self):
        long_swf = (
            '  This  is a    rather ' + self.format.bold('loooong ') +
            'string th' + self.format.green('at needs wrapppppp') + 'ing ')
        result = wrap(long_swf, width=11)
        # FIXME: this output might now be a bit too implementation specific!
        expected = [
            StringComponent(null_placeholder, 'This  is a'),
            StringComponent(null_placeholder, 'rather'),
            self.format.bold('loooong'),
            'string th' + self.format.green('at'),
            StringWithFormatting(self.format.green('needs wrapp')),
            self.format.green('pppp') + 'ing']
        self.assertEqual(result, expected)
