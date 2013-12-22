from unittest import TestCase
from io import StringIO

from junction.formatting import (
    Format, ParameterizingFormat, StringWithFormatting, TextWrapper, wrap)
from junction import Terminal, Fill

long_swf = (
    '  This is a    rather ' + Format('bold') + 'loooong ' + Format('normal') +
    'string that needs wrapppppping')


class TestFormattingBehviour(TestCase):
    def setUp(self):
        self.stream = StringIO()
        self.terminal = Terminal(stream=self.stream, force_styling=True)

    def test_default_formatting(self):
        fill = Fill()
        fill.default_format = Format('bold') + Format('green')
        fill.draw(3, 1, terminal=self.terminal)
        self.assertEqual(
            self.stream.getvalue(),
            self.terminal.bold + self.terminal.green +
            self.terminal.move(0, 0) + '...' + self.terminal.normal)


class TestFormat(TestCase):
    def test_len(self):
        self.assertEqual(len(Format('')), 0)
        self.assertEqual(len(Format('swift')), 0)

    def test_bool(self):
        self.assertTrue(bool(Format('')))
        self.assertTrue(bool(Format('swift')))

    def test_eq(self):
        self.assertEqual(Format('DAT'), Format('DAT'))
        self.assertNotEqual(Format('SAIT'), Format('8Track'))
        self.assertNotEqual(Format('Leotape'), 'not-a-format')

    def test_iter(self):
        f = Format('bob')
        for i, thing in enumerate(f):
            if i == 0:
                self.assertIs(thing, f)
            else:
                self.fail('iterating Format should only produce one item')

    def test_repr(self):
        self.assertEqual(repr(Format('hello')), "Format('hello')")

    def test_call_with_regular_content_string(self):
        f = Format('magic escape seq')
        result = f('printable text')
        self.assertIsInstance(result, StringWithFormatting)
        self.assertEqual(result, f + 'printable text' + Format('normal'))

    def test_draw(self):
        terminal = Terminal(force_styling=True)
        f = Format('blue')
        default = Format('red')
        self.assertEqual(f.draw(terminal, default), terminal.blue)
        f = Format('normal')
        # FIXME: I'm not sure I like this behaviour any more... might be better
        # to have composable format things that we can pass around as 'normal'
        self.assertEqual(f.draw(terminal, default), terminal.red)

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

    def test_split(self):
        f = Format('alice')
        self.assertEqual(f.split(), [f])
        self.assertIs(f.split()[0], f)


class TestParameterizingFormat(TestCase):
    def test_repr(self):
        f = ParameterizingFormat('something')
        self.assertEqual(repr(f), "ParameterizingFormat('something')")
        f(121, ['hello', 'world'])
        self.assertEqual(
            repr(f),
            "ParameterizingFormat('something')(121, ['hello', 'world'])")

    def test_eq(self):
        f = ParameterizingFormat('bob')
        self.assertEqual(f, ParameterizingFormat('bob'))
        f(7)
        self.assertNotEqual(f, ParameterizingFormat('bob'))
        self.assertEqual(f, ParameterizingFormat('bob')(7))
        self.assertNotEqual(f, 'not-a-parameterizing-string')

    def test_draw(self):
        terminal = Terminal(force_styling=True)
        f = ParameterizingFormat('cup')  # Must be legit curses cap
        self.assertEqual(f.draw(terminal), terminal.cup)
        f(1, 2)
        self.assertEqual(f.draw(terminal), terminal.cup(1, 2))


class TestStringWithFormatting(TestCase):
    def setUp(self):
        self.swf = 'Hello ' + Format('blue') + 'World!'

    def test_len(self):
        self.assertEqual(len(self.swf), len('Hello World!'))

    def test_str(self):
        self.assertEqual(str(self.swf), 'Hello World!')

    def test_repr(self):
        self.assertEqual(
            repr(self.swf),
            "StringWithFormatting('Hello ', Format('blue'), 'World!')")

    def test_draw(self):
        terminal = Terminal(force_styling=True)
        self.assertEqual(
            self.swf.draw(terminal),
            'Hello {}World!'.format(terminal.blue))

    def test_equality(self):
        self.assertEqual(self.swf, 'Hello ' + Format('blue') + 'World!')
        self.assertEqual(self.swf, StringWithFormatting(
            ('Hello ', Format('blue'), 'World!')))
        self.assertNotEqual(self.swf, StringWithFormatting('Hello World!'))
        self.assertNotEqual(self.swf, 'Hello World!')

    def test_addition(self):
        # String prefix
        long_swf = 'Prefix' + self.swf
        self.assertIsInstance(long_swf, StringWithFormatting)
        self.assertEqual(str(long_swf), 'PrefixHello World!')
        # Format prefix
        long_swf = Format('PrePrefixFormat') + long_swf
        self.assertIsInstance(long_swf, StringWithFormatting)
        self.assertEqual(long_swf._content, (
            Format('PrePrefixFormat'), 'PrefixHello ', Format('blue'),
            'World!'))
        # String suffix
        long_swf = self.swf + 'Suffix'
        self.assertIsInstance(long_swf, StringWithFormatting)
        self.assertEqual(str(long_swf), 'Hello World!Suffix')
        # Format suffix
        long_swf = long_swf + Format('SufSuffixFormat')
        self.assertEqual(long_swf._content, (
            'Hello ', Format('blue'), 'World!Suffix',
            Format('SufSuffixFormat')))
        # Adding two StringWithFormatting objects
        long_swf = self.swf + self.swf
        self.assertEqual(long_swf._content, (
            'Hello ', Format('blue'), 'World!Hello ', Format('blue'),
            'World!'))
        # Reverse-adding a str:
        long_swf = 'fantastic' + self.swf
        self.assertEqual(long_swf._content, (
            'fantasticHello ', Format('blue'), 'World!'))

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

    def test_split(self):
        result = long_swf.split()
        expected = [
            'This', 'is', 'a', 'rather', Format('bold'), 'loooong',
            Format('normal'), 'string', 'that', 'needs', 'wrapppppping']
        self.assertEqual(result, expected)


class TestTextWrapper(TestCase):
    def setUp(self):
        self.wrapper = TextWrapper(None)

    def test_chunk_str(self):
        normal = 'Bog-standard  string   with some spaces '
        result = list(self.wrapper._chunk(normal))
        expected = [
            'Bog-standard', '  ', 'string', '   ', 'with', ' ', 'some', ' ',
            'spaces', ' ']
        self.assertEqual(result, expected)

    def test_chunk_str_with_formatting(self):
        result = list(self.wrapper._chunk(long_swf))
        expected = [
            '  ', 'This', ' ', 'is', ' ', 'a', '    ', 'rather', ' ',
            Format('bold'), 'loooong', ' ', Format('normal'), 'string', ' ',
            'that', ' ', 'needs', ' ', 'wrapppppping']
        self.assertEqual(result, expected)

    def test_lstrip(self):
        chunks = ['  ', Format('a'), 'hello', ' ', 'world']
        self.wrapper._lstrip(chunks)
        expected = [Format('a'), 'hello', ' ', 'world']
        self.assertEqual(chunks, expected)

        chunks = [Format('a'), '  ', 'hello', ' ', 'world']
        self.wrapper._lstrip(chunks)
        self.assertEqual(chunks, expected)

        chunks = ['  ', Format('a'), '  ', 'hello', ' ', 'world']
        self.wrapper._lstrip(chunks)
        self.assertEqual(chunks, expected)

        chunks = [Format('a'), 'hello', ' ', 'world']
        self.wrapper._lstrip(chunks)
        self.assertEqual(chunks, expected)

        chunks = [' ', 'normal', ' ', 'string', ' ', 'with', ' ', 'spaces']
        self.wrapper._lstrip(chunks)
        expected = ['normal', ' ', 'string', ' ', 'with', ' ', 'spaces']
        self.assertEqual(chunks, expected)

    def test_rstrip(self):
        chunks = ['hello', ' ', 'world', Format('a'), '  ']
        self.wrapper._rstrip(chunks)
        expected = ['hello', ' ', 'world', Format('a')]
        self.assertEqual(chunks, expected)

        chunks = ['hello', ' ', 'world', '  ', Format('a')]
        self.wrapper._rstrip(chunks)
        self.assertEqual(chunks, expected)

        chunks = ['hello', ' ', 'world', '  ', Format('a'), '  ']
        self.wrapper._rstrip(chunks)
        self.assertEqual(chunks, expected)

        chunks = ['hello', ' ', 'world', Format('a')]
        self.wrapper._rstrip(chunks)
        self.assertEqual(chunks, expected)

        chunks = ['normal', ' ', 'string', ' ', 'with', ' ', 'spaces', ' ']
        self.wrapper._rstrip(chunks)
        expected = ['normal', ' ', 'string', ' ', 'with', ' ', 'spaces']
        self.assertEqual(chunks, expected)

    def test_wrap_str(self):
        text = 'The  quick brown fox jumps over the lazy dog'
        result = wrap(text, width=15)
        expected = [
            'The  quick',
            'brown fox jumps',
            'over the lazy',
            'dog']
        self.assertEqual(result, expected)
        self.assertEqual(wrap('', 10), [''])

    def test_wrap_str_with_formatting(self):
        result = wrap(long_swf, width=11)
        expected = [
            'This is a',
            'rather' + Format('bold'),
            'loooong' + Format('normal'),
            'string that',
            'needs wrapp',
            'pppping']
        self.assertEqual(result, expected)
        swf = Format('normal') + 'hello'
        result = wrap(swf, 3)
        expected = [StringWithFormatting((Format('normal'), 'hel')), 'lo']
        self.assertEqual(result, expected)
