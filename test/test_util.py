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

import asyncio
from unittest import TestCase

from jcn.util import (
    clamp, weighted_round_robin, crop_or_expand, LoopingCall,
    InheritDocstrings)


class TestUtil(TestCase):
    def test_clamp_values(self):
        self.assertEqual(clamp(1, 2, 3), 2)
        self.assertEqual(clamp(4, 3, 5), 4)
        self.assertEqual(clamp(10, 8, 9), 9)
        self.assertEqual(clamp(-1, 0, 1), 0)
        self.assertEqual(clamp(1, -1, 0), 0)

    def test_clamp_unbounded(self):
        self.assertEqual(clamp(42), 42)
        self.assertEqual(clamp(-42), -42)
        self.assertEqual(clamp(121, min_=13), 121)
        self.assertEqual(clamp(-121, min_=13), 13)
        self.assertEqual(clamp(121, max_=13), 13)
        self.assertEqual(clamp(-121, max_=13), -121)

    def test_weighted_round_robin(self):
        test_data = [('a', 3), ('b', 1), ('c', 2)]
        result = [
            val for val, _ in zip(weighted_round_robin(test_data), range(12))]
        expected = ['a', 'c', 'b', 'a', 'c', 'a'] * 2
        self.assertEqual(result, expected)

    def test_crop_or_expand_crop(self):
        self.assertEqual(crop_or_expand([1, 2, 3], 3), [1, 2, 3])
        self.assertEqual(crop_or_expand('abc', 3), 'abc')
        self.assertEqual(crop_or_expand([1, 2, 3, 4], 3), [1, 2, 3])
        self.assertEqual(crop_or_expand('abcd', 3), 'abc')
        self.assertEqual(crop_or_expand('abc', 2, scheme='beginning'), 'ab')
        self.assertEqual(
            crop_or_expand([1, 2, 3, 4], 3, scheme='end'),
            [2, 3, 4])
        self.assertEqual(crop_or_expand('abcd', 3, scheme='end'), 'bcd')
        self.assertEqual(
            crop_or_expand([1, 2, 3, 4, 5, 6], 2, scheme='middle'),
            [3, 4])
        self.assertEqual(crop_or_expand('abcdef', 2, scheme='middle'), 'cd')
        self.assertEqual(crop_or_expand('abcdef', 3, scheme='middle'), 'bcd')
        self.assertEqual(crop_or_expand('abcdefg', 3, scheme='middle'), 'cde')
        self.assertEqual(crop_or_expand('abcdefg', 2, scheme='middle'), 'cd')

    def test_crop_or_expand_expand(self):
        with self.assertRaises(TypeError):
            crop_or_expand([1, 2, 3], 4, default='bad')
        self.assertEqual(
            crop_or_expand([1, 2, 3], 4, default=['']),
            [1, 2, 3, ''])
        self.assertEqual(crop_or_expand('abc', 4), 'abc ')
        self.assertEqual(
            crop_or_expand([], 3, default=['moo']),
            ['moo', 'moo', 'moo'])
        self.assertEqual(crop_or_expand('', 2, default='baa'), 'baabaa')
        self.assertEqual(
            crop_or_expand([1], 5, scheme='end', default=['']),
            ['', '', '', '', 1])
        self.assertEqual(crop_or_expand('a', 6, scheme='end'), '     a')
        self.assertEqual(
            crop_or_expand([2], 5, default=[''], scheme='middle'),
            ['', '', 2, '', ''])
        self.assertEqual(
            crop_or_expand('z', 7, scheme='middle'),
            '   z   ')
        self.assertEqual(
            crop_or_expand([3], 4, default=[''], scheme='middle'),
            ['', '', 3, ''])
        self.assertEqual(
            crop_or_expand('y', 8, scheme='middle'),
            '    y   ')

    def test_looping_call(self):
        result = []
        future = asyncio.Future()
        def loopable(n):
            for i in range(n):
                yield result.append(i)
            looping_call.stop()
            future.set_result('done')
            yield result.append(n)
            # The following should never get called, seeing as we stopped the
            # looping call...
            yield result.append(n + 1)
        func = loopable(3).__next__
        looping_call = LoopingCall(func)
        loop = asyncio.get_event_loop()
        looping_call.start(0.01, loop=loop)
        loop.run_until_complete(future)
        self.assertEqual(result, [0, 1, 2, 3])

    def test_inherit_docstrings(self):
        class A(metaclass=InheritDocstrings):
            def foo(self):
                'foo docstring'

            def bar(self):
                pass

        class B(A):
            def foo(self):
                pass

            def bar(self):
                'bar docstring'

        self.assertEqual(B.foo.__doc__, 'foo docstring')
        self.assertEqual(B().foo.__doc__, 'foo docstring')
        self.assertEqual(B.bar.__doc__, 'bar docstring')
        self.assertEqual(B().bar.__doc__, 'bar docstring')

        class C(A):
            def foo(self):
                'new foo docstring'

        self.assertEqual(C.foo.__doc__, 'new foo docstring')
        self.assertEqual(C().foo.__doc__, 'new foo docstring')
