# coding=utf-8
from unittest import TestCase
from mock import Mock, patch, call
import asyncio

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
        patcher = patch.object(self.terminal, 'draw_lines', autospec=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_root(self):
        # To avoid artefacts from fullscreen contextmanager and the like:
        self.terminal._does_styling = False
        loop = asyncio.get_event_loop()
        fill = Fill()
        with patch('junction.Terminal.width', 4), patch(
                'junction.Terminal.height', 3):
            root = Root(fill, terminal=self.terminal, loop=loop)
            loop.call_soon(loop.stop)
            root.run()
        self.terminal.draw_lines.assert_called_with(
            ['....', '....', '....'], 0, 0, fill.default_format, None)
        fill2 = Fill()
        root.element = fill2
        self.assertIsNone(fill.root)
        self.assertIs(root.element, fill2)
        self.assertIs(fill2.root, root)

    def test_update(self):
        fill1 = Fill('1')
        fill1.default_format = 'oney'
        fill2 = Fill('2')
        fill1.default_format = 'twoey'
        stack = Stack(fill1, fill2)
        root = Root(stack, terminal=self.terminal)
        fill2.updated = True
        with self.assertRaises(ValueError):
            root.update()
        with patch('junction.Terminal.width', 2), patch(
                'junction.Terminal.height', 2):
            root.draw()
        self.terminal.draw_lines.assert_has_calls([
            call(['11'], 0, 0, fill1.default_format, None),
            call(['22'], 0, 1, fill2.default_format, None)])
        self.terminal.draw_lines.reset_mock()
        root.update()
        self.assertEqual(self.terminal.draw_lines.call_count, 0)
        fill2.updated = True
        root.update()
        self.terminal.draw_lines.assert_called_once_with(
            ['22'], 0, 1, fill2.default_format, None)

    def test_box(self):
        fill = Fill()
        box = Box(fill)
        blocks = box.draw(4, 4)
        self.assertCountEqual(blocks, [
            Block(1, 1, ['..', '..'], box.default_format),
            Block(0, 0, ['+--+'], box.default_format),
            Block(0, 1, ['|', '|'], box.default_format),
            Block(3, 1, ['|', '|'], box.default_format),
            Block(0, 3, ['+--+'], box.default_format)])
        box = Box(fill, chars='╓─┐│┘─╙║')
        blocks = box.draw(3, 3)
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
        blocks = stack.draw(5, 4)
        self.assertEqual(blocks, [
            Block(0, 0, ['11111'], fill1.default_format),
            Block(0, 1, ['22222', '22222'], fill2.default_format)])
        self.assertIsNone(stack.min_width)
        blocks = stack.draw(3, 2)
        self.assertEqual(blocks, [
            Block(0, 0, ['111'], fill1.default_format),
            Block(0, 1, ['222'], fill2.default_format)])
        blocks = stack.draw(4, 1)
        self.assertEqual(blocks, [
            Block(0, 0, ['1111'], fill1.default_format)])
        stack.valign = 'bottom'
        blocks = stack.draw(3, 2)
        self.assertEqual(blocks, [
            Block(0, 0, ['222', '222'], fill2.default_format)])
        fill3 = Fill('3', name='3')
        stack.add_element(fill3)
        blocks = stack.draw(5, 4)
        self.assertEqual(blocks, [
            Block(0, 3, ['33333'], fill3.default_format),
            Block(0, 1, ['22222', '22222'], fill2.default_format),
            Block(0, 0, ['11111'], fill1.default_format)])
        stack.remove_element(fill2)
        blocks = stack.draw(5, 4)
        self.assertEqual(blocks, [
            Block(0, 3, ['33333'], fill3.default_format),
            Block(0, 2, ['11111'], fill1.default_format)])

    def test_zebra(self):
        fill1 = Fill()
        fill2 = Fill(',')
        fill2.min_height = 2
        zebra = Zebra(
            fill1, fill1, fill1, fill2, fill1, even_format='hello',
            odd_format='world')
        blocks = zebra.draw(3, 10)
        self.assertEqual(blocks, [
            Block(0, 0, ['...'], 'hello'),
            Block(0, 1, ['...'], 'world'),
            Block(0, 2, ['...'], 'hello'),
            Block(0, 3, [',,,', ',,,'], 'world'),
            Block(0, 5, ['...'], 'hello')])
        zebra.even_format = None
        blocks = zebra.draw(3, 10)
        self.assertEqual(blocks, [
            Block(0, 0, ['...'], None),
            Block(0, 1, ['...'], 'world'),
            Block(0, 2, ['...'], None),
            Block(0, 3, [',,,', ',,,'], 'world'),
            Block(0, 5, ['...'], None)])
        zebra.default_format = 'norm'
        blocks = zebra.draw(3, 10)
        self.assertEqual(blocks, [
            Block(0, 0, ['...'], 'norm'),
            Block(0, 1, ['...'], 'world'),
            Block(0, 2, ['...'], 'norm'),
            Block(0, 3, [',,,', ',,,'], 'world'),
            Block(0, 5, ['...'], 'norm')])
