from unittest import TestCase
from mock import Mock, MagicMock, call

from junction.terminal import Terminal
from junction.display_elements import ABCDisplayElement, Fill, Text
from junction.container_elements import ABCContainerElement, Root, Stack


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


class TestDisplayElements(TestCase):
    def setUp(self):
        self.terminal = Terminal(force_styling=True)

    def test_set_get_alignment(self):
        fill = Fill()
        fill.valign = 'middle'
        self.assertEqual(fill.valign, 'middle')
        with self.assertRaises(ValueError):
            fill.valign = 'wrong'
        fill.halign = 'center'
        self.assertEqual(fill.halign, 'center')
        with self.assertRaises(ValueError):
            fill.halign = 'wrong'

    def test_fill(self):
        fill = Fill()
        self.assertEqual(fill._get_block(10, 0), [])
        self.assertEqual(fill._get_block(10, 1), ['..........'])
        self.assertEqual(fill._get_block(2, 2), ['..', '..'])
        self.assertEqual(fill._get_block(0, 4), ['', '', '', ''])
        fill = Fill('o')
        self.assertEqual(fill._get_block(1, 1), ['o'])

    def test_text(self):
        content = 'The quick brown fox jumps over the lazy dog'
        text = Text(content)
        expected = [
            'The quick brown  ',
            'fox jumps over   ',
            'the lazy dog     ',
            '                 ']
        self.assertEqual(
            text._get_cropped_block(17, 4), expected)
        text = Text(content, halign='center')
        expected = [
            ' The quick brown ',
            '  fox jumps over ',
            '   the lazy dog  ']
        self.assertEqual(text._get_cropped_block(17, 3), expected)
        text = Text(content, halign='right')
        expected = [
            '  The quick brown fox jumps',
            '          over the lazy dog']
        self.assertEqual(text._get_cropped_block(27, 2), expected)
        text = Text(content, valign='middle')
        expected = [
            ' ' * len(content),
            ' ' * len(content),
            content,
            ' ' * len(content)]
        self.assertEqual(text._get_cropped_block(len(content), 4), expected)
        text = Text(content, valign='bottom')
        expected = [
            '                 ',
            'The quick brown  ',
            'fox jumps over   ',
            'the lazy dog     ']
        self.assertEqual(text._get_cropped_block(17, 4), expected)
        text = Text(content, valign='bottom', fillchar='/')
        expected = [
            '/////////////////',
            'The quick brown//',
            'fox jumps over///',
            'the lazy dog/////']
        self.assertEqual(text._get_cropped_block(17, 4), expected)

    def test_text_with_formatting(self):
        content = (
            self.terminal.bold + 'The ' + self.terminal.normal + 'quick ' +
            self.terminal.red('brown') + ' fox ' +
            self.terminal.underline('jumps'))  # +
            #' over {t.green_on_white}the lazy{t.normal} dog'.format(
            #    t=self.terminal))
            # FIXME: can't yet handle .format insertion of Format objects into
            # strings
        text = Text(content)
        expected = [
            (self.terminal.bold + 'The ' + self.terminal.normal + 'quick ' +
             self.terminal.red + 'brown' + self.terminal.normal + '  '),
            ('fox ' + self.terminal.underline + 'jumps' +
             self.terminal.normal + self.terminal.normal + '        '),
            #+ ' over ' + self.terminal.green_on_white),
            #('the lazy' + self.terminal.normal + ' dog' +
            # self.terminal.normal + '     '),
            '                 ',
            '                 ']
        actual = text._get_cropped_block(17, 4)
        self.assertEqual(actual, expected)


class TestContainerElements(TestCase):
    def setUp(self):
        self.terminal = Mock(autospec=Terminal)
        self.terminal.fullscreen.return_value = MagicMock()

    def test_base_draw_and_update(self):
        element1 = DisplayElementForTest()
        element2 = DisplayElementForTest()
        container = ContainerElementForTest([element1, element2])
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
        fill = Fill()
        self.terminal.width = 4
        self.terminal.height = 4
        root = Root(fill, terminal=self.terminal)
        root.testing = True  # FIXME just whilst we're blocking with input()
        root.run()
        self.terminal.draw_block.assert_called_with(
            ['....', '....', '....', '....'], 0, 0, fill.default_format)

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
        stack = Stack([fill1, fill2])
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
