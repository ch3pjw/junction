from unittest import TestCase

from junction.elements import Fill, Text, VAlign, HAlign


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
