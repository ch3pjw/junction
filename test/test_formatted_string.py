from unittest import TestCase
#from mock import patch

from junction.formatting import Format, StringWithFormatting
#from junction import Terminal, Fill, Text, Stack


#class TestFormattingBehviour(TestCase):
#    def setUp(self):
#        self.terminal = Terminal(force_styling=True)
#
#    @patch('junction.Terminal.draw_block', autospec=True)
#    def _test_default_formatting(self, mock_draw_block):
#        fill = Fill()
#        fill.terminal = self.terminal
#        fill.default_format = self.terminal.bold + self.terminal.green
#        fill
#
#    def _test_formatting_in_content(self):
#        text = Text(
#            self.terminal.bold + 'The ' + self.terminal.normal + 'quick ' +
#            self.terminal.red('brown') + ' fox ' +
#            self.terminal.underline('jumps') +
#            ' over {t.green_on_white}the lazy{t.normal} dog'.format(
#                t=self.terminal))
#
#    def _test_default_formatting_inherited_in_container(self):
#        pass


class TestFormat(TestCase):
    def test_draw(self):
        f = Format('Some escape sequence')
        self.assertEqual(f.draw('Whatever is normal?'), 'Some escape sequence')
        f = Format(None)
        self.assertEqual(f.draw('Am I normal?'), 'Am I normal?')

    def test_equality(self):
        self.assertEqual(Format('foo'), Format('foo'))
        self.assertNotEqual(Format('foo'), Format('bar'))

    def test_addition(self):
        swf = Format('Hello') + 'World'
        self.assertIsInstance(swf, StringWithFormatting)
        self.assertIn(Format('Hello'), swf)
        self.assertIn('World', swf)
        swf = 'Hello' + Format('World')
        self.assertIsInstance(swf, StringWithFormatting)
        self.assertIn('Hello', swf)
        self.assertIn(Format('World'), swf)


class TestStringWithFormatting(TestCase):
    def setUp(self):
        self.swf = 'Hello ' + Format('hiding') + 'World!'

    def test_len(self):
        self.assertEqual(len(self.swf), len('Hello World!'))

    def test_str(self):
        self.assertEqual(str(self.swf), 'Hello World!')

    def test_draw(self):
        self.assertEqual(self.swf.draw('normal'), 'Hello hidingWorld!')

    def test_equality(self):
        self.assertEqual(self.swf, 'Hello ' + Format('hiding') + 'World!')
        self.assertEqual(self.swf, StringWithFormatting(
            ('Hello ', Format('hiding'), 'World!')))
        self.assertNotEqual(self.swf, StringWithFormatting('Hello World!'))

    def test_addition(self):
        # String prefix
        long_swf = 'Prefix' + self.swf
        self.assertIsInstance(long_swf, StringWithFormatting)
        self.assertEqual(str(long_swf), 'PrefixHello World!')
        # Format prefix
        long_swf = Format('PrePrefixFormat') + long_swf
        self.assertIsInstance(long_swf, StringWithFormatting)
        self.assertEqual(long_swf._content, (
            Format('PrePrefixFormat'), 'Prefix', 'Hello ', Format('hiding'),
            'World!'))
        # String suffix
        long_swf = self.swf + 'Suffix'
        self.assertIsInstance(long_swf, StringWithFormatting)
        self.assertEqual(str(long_swf), 'Hello World!Suffix')
        # Format suffix
        long_swf = long_swf + Format('SufSuffixFormat')
        self.assertEqual(long_swf._content, (
            'Hello ', Format('hiding'), 'World!', 'Suffix',
            Format('SufSuffixFormat')))
        # Adding two StringWithFormatting objects
        long_swf = self.swf + self.swf
        self.assertEqual(long_swf._content, (
            'Hello ', Format('hiding'), 'World!', 'Hello ', Format('hiding'),
            'World!'))

    def test_get_item_index(self):
        self.assertEqual(self.swf[2], 'l')
        self.assertEqual(self.swf[7], 'o')

    def test_get_item_slice(self):
        swf = 'Hello ' + Format('hiding1') + Format('hiding2') + 'World!'
        expected = 'lo ' + Format('hiding1') + Format('hiding2') + 'World!'
        self.assertEqual(swf[3:], expected)
        self.assertEqual(swf[3:100], expected)
        self.assertEqual(swf[3:len(self.swf)], expected)
        expected = 'o ' + Format('hiding1') + Format('hiding2') + 'Wor'
        self.assertEqual(swf[4:9], expected)
        expected = StringWithFormatting(['llo'])
        self.assertEqual(swf[2:5], expected)
        expected = StringWithFormatting(['llo '])
        self.assertEqual(swf[2:6], expected)
        expected = 'Hello ' + Format('hiding1') + Format('hiding2') + 'Wo'
        self.assertEqual(swf[:8], expected)
        expected = 'ello ' + Format('hiding1') + Format('hiding2') + 'Worl'
        self.assertEqual(swf[1:10], expected)
        expected = Format('hiding1') + Format('hiding2') + 'World'
        self.assertEqual(swf[6:11], expected)
        expected = Format('hiding1') + Format('hiding2') + 'orld!'
        self.assertEqual(swf[7:12], expected)
        expected = StringWithFormatting((Format('hiding1'), Format('hiding2')))
        self.assertEqual(swf[100:110], expected)
        swf = Format('one') + Format('two') + 'message'
        # FIXME: This is potentially leaky, as we just have to keep
        # concatenating every Format we have, because we don't know which ones
        # cancel each other out.
        expected = Format('one') + Format('two') + 'sage'
        self.assertEqual(swf[3:], expected)
