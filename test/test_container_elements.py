# coding=utf-8
from unittest import TestCase
from mock import Mock, patch
import asyncio
from io import StringIO

from junction.terminal import Terminal
from junction.root import Root
from junction.base import Block
from junction.display_elements import Fill, ABCDisplayElement
from junction.container_elements import Box, Stack, Zebra


class DisplayElementForTest(ABCDisplayElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._draw = Mock()

    def _get_block(self, *args, **kwargs):
        return ['hello', 'world']


class TestContainerElements(TestCase):
    def setUp(self):
        self.terminal = Terminal()
        self.stream = StringIO()
        self.terminal.stream = self.stream
        self.terminal.is_a_tty = False
        self.maxDiff = 0

    def test_root(self):
        loop = asyncio.get_event_loop()
        fill = Fill()
        with patch('junction.Terminal.width', 4), patch(
                'junction.Terminal.height', 3):
            root = Root(fill, terminal=self.terminal, loop=loop)
            loop.call_soon(loop.stop)
            root.run()
        self.assertIn(
            self.terminal.move(0, 0) + '....' +
            self.terminal.move(1, 0) + '....' +
            self.terminal.move(2, 0) + '....',
            self.terminal.stream.getvalue())
        fill2 = Fill()
        root.element = fill2
        self.assertIsNone(fill.root)
        self.assertIs(root.element, fill2)
        self.assertIs(fill2.root, root)

    def test_box(self):
        fill = Fill()
        box = Box(fill)
        blocks = box.get_all_blocks(4, 4)
        self.assertCountEqual(blocks, [
            Block(1, 1, ['..', '..'], box.default_format),
            Block(0, 0, ['+--+'], box.default_format),
            Block(0, 1, ['|', '|'], box.default_format),
            Block(3, 1, ['|', '|'], box.default_format),
            Block(0, 3, ['+--+'], box.default_format)])
        box = Box(fill, chars='╓─┐│┘─╙║')
        blocks = box.get_all_blocks(3, 3)
        self.assertCountEqual(blocks, [
            Block(1, 1, ['.'], box.default_format),
            Block(0, 0, ['╓─┐'], box.default_format),
            Block(0, 1, ['║'], box.default_format),
            Block(2, 1, ['│'], box.default_format),
            Block(0, 2, ['╙─┘'], box.default_format)])
        box = Box(fill, chars='[]')
        self.assertEqual(box.chars, '+-+|+-+|')

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
        blocks = stack.get_all_blocks(5, 4)
        self.assertEqual(blocks, [
            Block(0, 0, ['11111'], fill1.default_format),
            Block(0, 1, ['22222', '22222'], fill2.default_format)])
        self.assertIsNone(stack.min_width)
        blocks = stack.get_all_blocks(3, 2)
        self.assertEqual(blocks, [
            Block(0, 0, ['111'], fill1.default_format),
            Block(0, 1, ['222'], fill2.default_format)])
        blocks = stack.get_all_blocks(4, 1)
        self.assertEqual(blocks, [
            Block(0, 0, ['1111'], fill1.default_format)])
        stack.valign = 'bottom'
        blocks = stack.get_all_blocks(3, 2)
        self.assertEqual(blocks, [
            Block(0, 0, ['222', '222'], fill2.default_format)])
        fill3 = Fill('3', name='3')
        stack.add_element(fill3)
        blocks = stack.get_all_blocks(5, 4)
        self.assertEqual(blocks, [
            Block(0, 3, ['33333'], fill3.default_format),
            Block(0, 1, ['22222', '22222'], fill2.default_format),
            Block(0, 0, ['11111'], fill1.default_format)])
        stack.remove_element(fill2)
        blocks = stack.get_all_blocks(5, 4)
        self.assertEqual(blocks, [
            Block(0, 3, ['33333'], fill3.default_format),
            Block(0, 2, ['11111'], fill1.default_format)])

    def test_update_stack(self):
        fill1 = Fill('1')
        fill2 = Fill('2')
        stack = Stack(fill1, fill2)
        blocks = stack.get_all_blocks(3, 2)
        self.assertEqual(blocks, [
            Block(0, 0, ['111'], None),
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
        self.assertCountEqual(blocks, [
            Block(0, 0, ['11'], 'format_one'),
            Block(0, 1, ['22'], 'format_two')])
        blocks = stack.get_updated_blocks()
        self.assertEqual(blocks, [])
        fill2.updated = True
        blocks = stack.get_updated_blocks()
        self.assertCountEqual(blocks, [
            Block(0, 1, ['22'], fill2.default_format)])

    def test_zebra(self):
        fill1 = Fill()
        fill2 = Fill(',')
        fill2.min_height = 2
        zebra = Zebra(
            fill1, fill1, fill1, fill2, fill1, even_format='hello',
            odd_format='world')
        blocks = zebra.get_all_blocks(3, 10)
        self.assertEqual(blocks, [
            Block(0, 0, ['...'], 'hello'),
            Block(0, 1, ['...'], 'world'),
            Block(0, 2, ['...'], 'hello'),
            Block(0, 3, [',,,', ',,,'], 'world'),
            Block(0, 5, ['...'], 'hello')])
        zebra.even_format = None
        blocks = zebra.get_all_blocks(3, 10)
        self.assertEqual(blocks, [
            Block(0, 0, ['...'], None),
            Block(0, 1, ['...'], 'world'),
            Block(0, 2, ['...'], None),
            Block(0, 3, [',,,', ',,,'], 'world'),
            Block(0, 5, ['...'], None)])
        zebra.default_format = 'norm'
        blocks = zebra.get_all_blocks(3, 10)
        self.assertEqual(blocks, [
            Block(0, 0, ['...'], 'norm'),
            Block(0, 1, ['...'], 'normworld'),
            Block(0, 2, ['...'], 'norm'),
            Block(0, 3, [',,,', ',,,'], 'normworld'),
            Block(0, 5, ['...'], 'norm')])
