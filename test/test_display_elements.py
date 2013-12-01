from unittest import TestCase

from junction.terminal import Terminal
from junction.display_elements import Fill, Text


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
