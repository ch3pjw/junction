from unittest import TestCase
from mock import Mock, call

from junction.terminal import Terminal
from junction.display_elements import Fill, Text
from junction.container_elements import Stack


class TestElements(TestCase):
    def setUp(self):
        self.terminal = Mock(autospec=Terminal)

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

    def test_root(self):
        pass

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
        fill2 = Fill('2', name='2')
        fill2.min_height = 2
        stack = Stack([fill1, fill2])
        stack.terminal = self.terminal
        stack.draw(5, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['11111'], 0, 0),
            call(['22222', '22222'], 0, 1)])
        self.terminal.draw_block.reset_mock()
        self.assertIsNone(stack.min_width)
        stack.draw(3, 2)
        self.terminal.draw_block.assert_has_calls([
            call(['111'], 0, 0),
            call(['222'], 0, 1)])
        self.terminal.draw_block.reset_mock()
        stack.draw(4, 1)
        self.terminal.draw_block.assert_has_calls([
            call(['1111'], 0, 0)])
        self.terminal.draw_block.reset_mock()
        stack.valign = 'bottom'
        stack.draw(3, 2)
        self.terminal.draw_block.assert_has_calls([
            call(['222', '222'], 0, 0)])
        self.terminal.draw_block.reset_mock()
        fill3 = Fill('3', name='3')
        stack.add_element(fill3)
        stack.draw(5, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['33333'], 0, 3),
            call(['22222', '22222'], 0, 1),
            call(['11111'], 0, 0)])
        self.terminal.draw_block.reset_mock()
        stack.remove_element(fill2)
        stack.draw(5, 4)
        self.terminal.draw_block.assert_has_calls([
            call(['33333'], 0, 3),
            call(['11111'], 0, 2)])
        self.terminal.draw_block.reset_mock()
