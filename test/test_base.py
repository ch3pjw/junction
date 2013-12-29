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

from junction.base import ABCUIElement, Block


class TestABCUIElement(TestCase):
    def test_repr(self):
        class MyElement(ABCUIElement):
            def _get_all_blocks(self, *args, **kwargs):
                pass

            def _get_updated_blocks(self, *args, **kwargs):
                pass
        my_element = MyElement()
        self.assertIn('MyElement element', repr(my_element))
        my_element = MyElement(name='testing')
        self.assertIn('MyElement element', repr(my_element))
        self.assertIn('testing', repr(my_element))


class TestBlock(TestCase):
    def test_repr(self):
        block = Block(1, 2, ['hello', 'world'], None)
        self.assertEqual(repr(block), "Block(1, 2, ['hello', 'world'])")
        block = Block(3, 4, ['Milton', 'Jones'], 'spangly')
        self.assertEqual(
            repr(block), "Block(3, 4, ['Milton', 'Jones'], 'spangly')")
