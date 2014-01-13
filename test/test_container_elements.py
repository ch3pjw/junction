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

# coding=utf-8
from unittest import TestCase
from mock import patch
import asyncio
from io import StringIO

from jcn.terminal import Terminal
from jcn.root import Root
from jcn.base import Block
from jcn.display_elements import Fill
from jcn.container_elements import Box, Stack, Zebra, VerticalSplitContainer


class TestBase(TestCase):
    def test_add_element(self):
        fill1 = Fill('1')
        container = Stack()
        self.assertIsNone(container.active_element)
        container.add_element(fill1)
        self.assertEqual(len(container), 1)
        self.assertIn(fill1, container)
        self.assertIs(container.active_element, fill1)
        fill2 = Fill('2')
        container.add_element(fill2)
        self.assertEqual(len(container), 2)
        self.assertIn(fill2, container)
        self.assertIs(container.active_element, fill1)

    def test_remove_element(self):
        container = Stack()
        fill1 = Fill('1')
        fill2 = Fill('2')
        with self.assertRaises(ValueError):
            container.remove_element(fill1)
        container = Stack(fill1, fill2)
        self.assertEqual(len(container), 2)
        container.remove_element(fill1)
        self.assertEqual(len(container), 1)
        self.assertIn(fill2, container)
        self.assertIsNone(container.active_element)

    def test_replace_element(self):
        fill1 = Fill('1', name='1')
        fill2 = Fill('2', name='2')
        fill3 = Fill('3', name='3')
        container = Stack(fill1, fill2)
        self.assertEqual(len(container), 2)
        container.replace_element(fill1, fill3)
        self.assertEqual(len(container), 2)
        self.assertNotIn(fill1, container)
        self.assertIs(container[0], fill3)


class ContainerElementTestCase(TestCase):
    def setUp(self):
        self.terminal = Terminal()
        self.stream = StringIO()
        self.terminal.stream = self.stream
        self.terminal.is_a_tty = False
        self.maxDiff = 0

    def check_get_all_blocks(self, element, width, height, expected):
        blocks = element.get_all_blocks(width, height)
        for block in expected:
            self.assertIn(block, blocks)


class TestRoot(ContainerElementTestCase):
    def test_root(self):
        loop = asyncio.get_event_loop()
        fill = Fill()
        with patch('jcn.Terminal.width', 4), patch(
                'jcn.Terminal.height', 3):
            root = Root(fill, terminal=self.terminal, loop=loop)
            loop.call_soon(loop.stop)
            root.run()
        self.assertIn(
            self.terminal.move(0, 0) + self.terminal.normal + '....' +
            self.terminal.move(1, 0) + self.terminal.normal + '....' +
            self.terminal.move(2, 0) + self.terminal.normal + '....',
            self.terminal.stream.getvalue())
        fill2 = Fill()
        root.element = fill2
        self.assertIsNone(fill.root)
        self.assertIs(root.element, fill2)
        self.assertIs(fill2.root, root)


class TestBox(ContainerElementTestCase):
    def test_box(self):
        fill = Fill()
        box = Box(fill)
        self.check_get_all_blocks(
            box, 4, 4,
            [Block(1, 1, ['..', '..'], box.default_format),
             Block(0, 0, ['+--+'], box.default_format),
             Block(0, 1, ['|', '|'], box.default_format),
             Block(3, 1, ['|', '|'], box.default_format),
             Block(0, 3, ['+--+'], box.default_format)])
        box = Box(fill, chars='╓─┐│┘─╙║')
        self.check_get_all_blocks(
            box, 3, 3,
            [Block(1, 1, ['.'], box.default_format),
             Block(0, 0, ['╓─┐'], box.default_format),
             Block(0, 1, ['║'], box.default_format),
             Block(2, 1, ['│'], box.default_format),
             Block(0, 2, ['╙─┘'], box.default_format)])
        box = Box(fill, chars='[]')
        self.assertEqual(box.chars, '+-+|+-+|')


class TestStack(ContainerElementTestCase):
    def test_stack_limits(self):
        stack = Stack()
        self.assertEqual(stack.min_height, 0)
        fill1 = Fill('1')
        fill2 = Fill('2')
        stack.add_element(fill1)
        stack.add_element(fill2)
        self.assertEqual(stack.min_height, 2)
        fill2.min_height = 2
        self.assertEqual(stack.min_height, 3)
        self.assertIsNone(stack.min_width)
        fill1.min_width = 7
        self.assertEqual(stack.min_width, 7)

    def test_stack_alignment(self):
        stack = Stack()
        with self.assertRaises(ValueError):
            stack.valign = 'middle'

    def test_stack(self):
        fill1 = Fill('1', name='1')
        fill1.default_format = 'kinda oney'
        fill2 = Fill('2', name='2')
        fill2.default_format = 'more like two'
        fill2.min_height = 2
        stack = Stack(fill1, fill2)
        self.check_get_all_blocks(
            stack, 5, 4,
            [Block(0, 0, ['11111'], fill1.default_format),
             Block(0, 1, ['22222', '22222'], fill2.default_format)])
        self.assertIsNone(stack.min_width)
        self.check_get_all_blocks(
            stack, 3, 2,
            [Block(0, 0, ['111'], fill1.default_format),
             Block(0, 1, ['222'], fill2.default_format)])
        self.check_get_all_blocks(
            stack, 4, 1,
            [Block(0, 0, ['1111'], fill1.default_format)])
        stack.valign = 'bottom'
        self.check_get_all_blocks(
            stack, 3, 2,
            [Block(0, 0, ['222', '222'], fill2.default_format)])
        fill3 = Fill('3', name='3')
        stack.add_element(fill3)
        self.check_get_all_blocks(
            stack, 5, 4,
            [Block(0, 3, ['33333'], fill3.default_format),
             Block(0, 1, ['22222', '22222'], fill2.default_format),
             Block(0, 0, ['11111'], fill1.default_format)])
        stack.remove_element(fill2)
        self.check_get_all_blocks(
            stack, 5, 4,
            [Block(0, 3, ['33333'], fill3.default_format),
             Block(0, 2, ['11111'], fill1.default_format)])

    def test_update_stack(self):
        fill1 = Fill('1')
        fill2 = Fill('2')
        stack = Stack(fill1, fill2)
        self.check_get_all_blocks(
            stack, 3, 2,
            [Block(0, 0, ['111'], None),
             Block(0, 1, ['222'], None)])
        fill2.default_format = 'new!'
        blocks = stack.get_updated_blocks()
        self.assertEqual(blocks, [Block(0, 1, ['222'], 'new!')])

    def test_update(self):
        fill1 = Fill('1')
        fill1.default_format = 'format_one'
        fill2 = Fill('2')
        fill2.default_format = 'format_two'
        stack = Stack(fill1, fill2)
        fill2.updated = True
        with self.assertRaises(ValueError):
            stack.get_updated_blocks()
        blocks = stack.get_all_blocks(2, 2)
        self.check_get_all_blocks(
            stack, 2, 2,
            [Block(0, 0, ['11'], 'format_one'),
             Block(0, 1, ['22'], 'format_two')])
        blocks = stack.get_updated_blocks()
        self.assertEqual(blocks, [])
        fill2.updated = True
        blocks = stack.get_updated_blocks()
        self.assertCountEqual(blocks, [
            Block(0, 1, ['22'], fill2.default_format)])


class TestZebra(ContainerElementTestCase):
    def test_zebra(self):
        fill1 = Fill()
        fill2 = Fill(',')
        fill2.min_height = 2
        zebra = Zebra(
            fill1, fill1, fill1, fill2, fill1, even_format='hello',
            odd_format='world')
        self.check_get_all_blocks(
            zebra, 3, 10,
            [Block(0, 0, ['...'], 'hello'),
             Block(0, 1, ['...'], 'world'),
             Block(0, 2, ['...'], 'hello'),
             Block(0, 3, [',,,', ',,,'], 'world'),
             Block(0, 5, ['...'], 'hello')])
        zebra.even_format = None
        self.check_get_all_blocks(
            zebra, 3, 10,
            [Block(0, 0, ['...'], None),
             Block(0, 1, ['...'], 'world'),
             Block(0, 2, ['...'], None),
             Block(0, 3, [',,,', ',,,'], 'world'),
             Block(0, 5, ['...'], None)])
        zebra.default_format = 'norm'
        self.check_get_all_blocks(
            zebra, 3, 10,
            [Block(0, 0, ['...'], 'norm'),
             Block(0, 1, ['...'], 'normworld'),
             Block(0, 2, ['...'], 'norm'),
             Block(0, 3, [',,,', ',,,'], 'normworld'),
             Block(0, 5, ['...'], 'norm')])


class TestVerticalSplitContainer(ContainerElementTestCase):
    def test_basic(self):
        fill1 = Fill('1')
        vsplit = VerticalSplitContainer(fill1)
        self.check_get_all_blocks(
            vsplit, 3, 1,
            [Block(0, 0, ['111'], None)])
        fill2 = Fill('2')
        vsplit.add_element(fill2)
        self.check_get_all_blocks(
            vsplit, 5, 2,
            [Block(0, 0, ['111', '111'], None),
             Block(3, 0, ['22', '22'], None)])
        fill3 = Fill('3')
        vsplit.add_element(fill3, weight=2)
        self.check_get_all_blocks(
            vsplit, 8, 1,
            [Block(0, 0, ['11'], None),
             Block(2, 0, ['22'], None),
             Block(4, 0, ['3333'], None)])
        vsplit.remove_element(fill2)
        self.check_get_all_blocks(
            vsplit, 3, 1,
            [Block(0, 0, ['1'], None),
             Block(1, 0, ['33'], None)])

    def test_constraints(self):
        fill1 = Fill('1', name='1')
        fill2 = Fill('2', name='2')
        fill3 = Fill('3', name='3')
        fill3.max_width = 2
        vsplit = VerticalSplitContainer(fill1, fill2, fill3)
        self.check_get_all_blocks(
            vsplit, 9, 1,
            [Block(0, 0, ['1111'], None),
             Block(4, 0, ['222'], None),
             Block(7, 0, ['33'], None)])
        self.check_get_all_blocks(
            vsplit, 3, 1,
            [Block(0, 0, ['1'], None),
             Block(1, 0, ['2'], None),
             Block(2, 0, ['3'], None)])
        fill3.max_width = None
        fill3.min_width = 3
        # FIXME: what to do when width is too small?
        #blocks = vsplit.get_all_blocks(2, 1)
        #self.assertEqual(blocks, [
        #    Block(0, 0, ['1'], None),
        #    Block(1, 0, ['2'], None)])
        self.check_get_all_blocks(
            vsplit, 5, 1,
            [Block(0, 0, ['1'], None),
             Block(1, 0, ['2'], None),
             Block(2, 0, ['333'], None)])
        self.check_get_all_blocks(
            vsplit, 12, 1,
            [Block(0, 0, ['1111'], None),
             Block(4, 0, ['2222'], None),
             Block(8, 0, ['3333'], None)])
        fill3.min_width = fill3.max_width = 5
        self.check_get_all_blocks(
            vsplit, 7, 1,
            [Block(0, 0, ['1'], None),
             Block(1, 0, ['2'], None),
             Block(2, 0, ['33333'], None)])
        self.check_get_all_blocks(
            vsplit, 19, 1,
            [Block(0, 0, ['1111111'], None),
             Block(7, 0, ['2222222'], None),
             Block(14, 0, ['33333'], None)])
        # Blocks may get more than they asked for, if we have surplus space to
        # allocate:
        vsplit.remove_element(fill2)
        fill1.min_width = 3
        self.check_get_all_blocks(
            vsplit, 10, 1,
            [Block(0, 0, ['11111'], None),
             Block(5, 0, ['33333'], None)])

    def test_max_width(self):
        fill1 = Fill('1')
        fill1.max_width = 30
        fill2 = Fill('2')
        vsplit = VerticalSplitContainer(fill1, fill2)
        self.assertIsNone(vsplit.max_width)
        fill2.max_width = 12
        self.assertEqual(vsplit.max_width, 42)

    def test_min_width(self):
        fill1 = Fill('1')
        fill1.min_width = 7
        fill2 = Fill('2')
        vsplit = VerticalSplitContainer(fill1, fill2)
        self.assertEqual(vsplit.min_width, 7)
        fill2.min_width = 35
        self.assertEqual(vsplit.min_width, 42)
