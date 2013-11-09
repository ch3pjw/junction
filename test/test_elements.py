from unittest import TestCase

from junction.util import VAlign, HAlign
from junction.elements import Fill, Text, Stack


class TestElements(TestCase):
    def test_fill(self):
        fill = Fill()
        self.assertEqual(fill.draw(10, 0), [])
        self.assertEqual(fill.draw(10, 1), ['..........'])
        self.assertEqual(fill.draw(2, 2), ['..', '..'])
        self.assertEqual(fill.draw(0, 4), ['', '', '', ''])
        fill = Fill('o')
        self.assertEqual(fill.draw(1, 1), ['o'])

    def test_text(self):
        content = 'The quick brown fox jumps over the lazy dog'
        text = Text(content)
        expected = [
            'The quick brown  ',
            'fox jumps over   ',
            'the lazy dog     ',
            '                 ']
        self.assertEqual(text.draw(17, 4), expected)
        text = Text(content, halign=HAlign.center)
        expected = [
            ' The quick brown ',
            '  fox jumps over ',
            '   the lazy dog  ']
        self.assertEqual(text.draw(17, 3), expected)
        text = Text(content, halign=HAlign.right)
        expected = [
            '  The quick brown fox jumps',
            '          over the lazy dog']
        self.assertEqual(text.draw(27, 2), expected)
        text = Text(content, valign=VAlign.middle)
        expected = [
            ' ' * len(content),
            content,
            ' ' * len(content),
            ' ' * len(content)]
        self.assertEqual(text.draw(len(content), 4), expected)
        text = Text(content, valign=VAlign.bottom)
        expected = [
            '                 ',
            'The quick brown  ',
            'fox jumps over   ',
            'the lazy dog     ']
        self.assertEqual(text.draw(17, 4), expected)
        text = Text(content, valign=VAlign.bottom, fillchar='/')
        expected = [
            '/////////////////',
            'The quick brown//',
            'fox jumps over///',
            'the lazy dog/////']
        self.assertEqual(text.draw(17, 4), expected)

    def test_stack(self):
        fill1 = Fill('1')
        fill2 = Fill('2')
        fill2.min_height = 2
        stack = Stack([fill1, fill2])
        self.assertEqual(
            stack.draw(5, 4), ['     ', '11111', '22222', '22222'])
        self.assertEqual(stack.min_height, 3)
        self.assertIsNone(stack.min_width)
        fill2.min_width = 7
        self.assertEqual(stack.min_width, 7)
        self.assertEqual(stack.draw(3, 2), ['111', '222'])
        self.assertEqual(stack.draw(3, 1), ['111'])
        fill3 = Fill('3')
        stack.add_element(fill3)
        self.assertEqual(
            stack.draw(5, 4), ['11111', '22222', '22222', '33333'])
        stack.remove_element(fill2)
        stack.valign = VAlign.middle
        self.assertEqual(stack.draw(2, 4), ['  ', '11', '33', '  '])
