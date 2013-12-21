# coding=utf-8
from unittest import TestCase
from mock import Mock, patch, call
import asyncio

from junction.terminal import Terminal
from junction.root import Root
from junction.display_elements import Fill, ABCDisplayElement
from junction.container_elements import (
    ABCContainerElement, Box, Stack, Zebra)


class DisplayElementForTest(ABCDisplayElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._draw = Mock()

    def _get_block(self, *args, **kwargs):
        return ['hello', 'world']


class ContainerElementForTest(ABCContainerElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terminal = Mock()

    def _get_elements_sizes_and_positions(self, width, height, x, y):
        for element in self:
            yield element, width, height, x, y


class TestContainerElements(TestCase):
    def setUp(self):
        self.terminal = Terminal()
        patcher = patch.object(self.terminal, 'draw_block', autospec=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_base_draw_and_update(self):
        element1 = DisplayElementForTest()
        element2 = DisplayElementForTest()
        container = ContainerElementForTest(element1, element2)
        with self.assertRaises(ValueError):
            container.update()
        container.draw(1, 2, 3, 4, 'bottom', 'right')
        element1._draw.assert_called_once_with(1, 2, 3, 4, 'bottom', 'right')
        element2._draw.assert_called_once_with(1, 2, 3, 4, 'bottom', 'right')
        element1._draw.reset_mock()
        element2._draw.reset_mock()
        element2.updated = True
        container.update()
        self.assertEqual(element1._draw.call_count, 0)
        element2._draw.assert_called_once_with(1, 2, 3, 4, 'bottom', 'right')
        self.assertFalse(element2.updated)

    def test_root(self):
        # To avoid artefacts from fullscreen contextmanager and the like:
        self.terminal._does_styling = False
        loop = asyncio.get_event_loop()
        fill = Fill()
        with patch('junction.Terminal.width', 4), patch(
                'junction.Terminal.height', 3):
            root = Root(fill, terminal=self.terminal, loop=loop)
            loop.call_soon(loop.stop)
            # FIXME: this won't run in a git hook atm because stdin is
            # different somehow, so we can't attach an input reader - need to
            # investigate more...
            root.run()
            self.terminal.draw_block.assert_called_with(
                ['....', '....', '....'], 0, 0, fill.default_format)

    def test_box(self):
        fill = Fill()
        box = Box(fill)
        box.terminal = self.terminal
        box.draw(4, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['..', '..'], 1, 1, box.default_format),
            call(['+--+'], 0, 0, box.default_format),
            call(['|', '|'], 0, 1, box.default_format),
            call(['|', '|'], 3, 1, box.default_format),
            call(['+--+'], 0, 3, box.default_format)],
            any_order=True)
        self.terminal.draw_block.reset_mock()
        box = Box(fill, chars='╓─┐│┘─╙║')
        box.terminal = self.terminal
        box.draw(3, 3)
        self.terminal.draw_block.assert_has_calls([
            call(['.'], 1, 1, box.default_format),
            call(['╓─┐'], 0, 0, box.default_format),
            call(['║'], 0, 1, box.default_format),
            call(['│'], 2, 1, box.default_format),
            call(['╙─┘'], 0, 2, box.default_format)],
            any_order=True)
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
        stack.terminal = self.terminal
        stack.draw(5, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['11111'], 0, 0, fill1.default_format),
            call(['22222', '22222'], 0, 1, fill2.default_format)])
        self.terminal.draw_block.reset_mock()
        self.assertIsNone(stack.min_width)
        stack.draw(3, 2)
        self.terminal.draw_block.assert_has_calls([
            call(['111'], 0, 0, fill1.default_format),
            call(['222'], 0, 1, fill2.default_format)])
        self.terminal.draw_block.reset_mock()
        stack.draw(4, 1)
        self.terminal.draw_block.assert_has_calls([
            call(['1111'], 0, 0, fill1.default_format)])
        self.terminal.draw_block.reset_mock()
        stack.valign = 'bottom'
        stack.draw(3, 2)
        self.terminal.draw_block.assert_has_calls([
            call(['222', '222'], 0, 0, fill2.default_format)])
        self.terminal.draw_block.reset_mock()
        fill3 = Fill('3', name='3')
        stack.add_element(fill3)
        stack.draw(5, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['33333'], 0, 3, fill3.default_format),
            call(['22222', '22222'], 0, 1, fill2.default_format),
            call(['11111'], 0, 0, fill1.default_format)])
        self.terminal.draw_block.reset_mock()
        stack.remove_element(fill2)
        stack.draw(5, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['33333'], 0, 3, fill3.default_format),
            call(['11111'], 0, 2, fill1.default_format)])
        self.terminal.draw_block.reset_mock()

    def test_zebra(self):
        fill1 = Fill()
        fill2 = Fill(',')
        fill2.min_height = 2
        zebra = Zebra(
            fill1, fill1, fill1, fill2, fill1, even_format='hello',
            odd_format='world')
        zebra.terminal = self.terminal
        zebra.draw(3, 10)
        self.terminal.draw_block.assert_has_calls([
            call(['...'], 0, 0, 'hello'),
            call(['...'], 0, 1, 'world'),
            call(['...'], 0, 2, 'hello'),
            call([',,,', ',,,'], 0, 3, 'world'),
            call(['...'], 0, 5, 'hello')])
        self.terminal.draw_block.reset_mock()
        zebra.even_format = None
        zebra.draw(3, 10)
        self.terminal.draw_block.assert_has_calls([
            call(['...'], 0, 0, self.terminal._normal),
            call(['...'], 0, 1, 'world'),
            call(['...'], 0, 2, self.terminal._normal),
            call([',,,', ',,,'], 0, 3, 'world'),
            call(['...'], 0, 5, self.terminal._normal)])
        self.terminal.draw_block.reset_mock()
        zebra.default_format = 'norm'
        zebra.draw(3, 10)
        self.terminal.draw_block.assert_has_calls([
            call(['...'], 0, 0, 'norm'),
            call(['...'], 0, 1, 'world'),
            call(['...'], 0, 2, 'norm'),
            call([',,,', ',,,'], 0, 3, 'world'),
            call(['...'], 0, 5, 'norm')])
