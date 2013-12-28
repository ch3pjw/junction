from unittest import TestCase
from io import StringIO

from junction.formatting import (
    StringComponentSpec, NullComponentSpec, FormatPlaceholder,
    StylePlaceholder, FormatSpecFactory, StyleSpecFactory,
    StringWithFormatting, wrap)
from junction import Terminal, Text


class TestStringComponentSpec(TestCase):
    def setUp(self):
        class TestClass(StringComponentSpec):
            def _populate(self):
                pass
        self.test_cls = TestClass

    def test_early_addition_exception(self):
        with self.assertRaises(ValueError):
            self.test_cls('red') + 'hello'
        with self.assertRaises(ValueError):
            'world' + self.test_cls('red')

    def test_too_many_content_calls(self):
        with self.assertRaises(ValueError):
            self.test_cls('red')('content')('more content')

    def test_len(self):
        self.assertEqual(len(self.test_cls('blue')('content')), 7)

    def test_str(self):
        self.assertEqual(str(self.test_cls('blue')('content')), 'content')

    def test_repr(self):
        self.assertEqual(
            repr(self.test_cls('green')('beret')),
            "TestClass('green', 'beret')")

    def test_getattr(self):
        spec = self.test_cls('bold')('  Hello!  ')
        self.assertEqual(spec.strip(), self.test_cls('bold')('Hello!'))


class TestParameterizingSpec(TestCase):
    def setUp(self):
        self.terminal = Terminal(force_styling=True)
        self.factory = FormatSpecFactory()

    def test_too_many_calls(self):
        parameterizing_format_spec = self.factory.color(230)
        with self.assertRaises(ValueError):
            parameterizing_format_spec('user content')('extra call')

    def test_populate(self):
        parameterizing_format_spec = self.factory.color
        with self.assertRaises(ValueError):
            parameterizing_format_spec.populate(self.terminal)
        parameterizing_format_spec(121)('important info')
        result = parameterizing_format_spec.populate(self.terminal)
        self.assertEqual(result, self.terminal.color(121) + 'important info')


class TestNullComponent(TestCase):
    def test_equal(self):
        self.assertEqual(
            NullComponentSpec('hello'), NullComponentSpec('hello'))
        self.assertNotEqual(
            NullComponentSpec('hello'), NullComponentSpec('world'))


class TestPlaceholder(TestCase):
    def setUp(self):
        self.terminal = Terminal(force_styling=True)
        self.styles = {
            'heading': FormatPlaceholder('underline'),
            'h1': StylePlaceholder('heading'),
            'h2': StylePlaceholder('heading') + FormatPlaceholder('red')}

    def test_populate_format_placeholder(self):
        format_placeholder = FormatPlaceholder('red')
        result = format_placeholder.populate(self.terminal)
        self.assertEqual(result, self.terminal.red)

    def test_populate_style_placeholder_simple(self):
        style_placeholder = StylePlaceholder('heading')
        result = style_placeholder.populate(self.styles, self.terminal)
        self.assertEqual(result, self.terminal.underline)

    def test_populate_style_placeholder_style_ref(self):
        style_placeholder = StylePlaceholder('h1')
        result = style_placeholder.populate(self.styles, self.terminal)
        self.assertEqual(result, self.terminal.underline)

    def test_populate_style_placeholder_compound(self):
        style_placeholder = StylePlaceholder('h2')
        result = style_placeholder.populate(self.styles, self.terminal)
        self.assertEqual(result, self.terminal.underline + self.terminal.red)


class TestStringWithFormatting(TestCase):
    def setUp(self):
        self.format = FormatSpecFactory()
        self.style = StyleSpecFactory()
        self.swf = 'Hello ' + self.format.blue(self.format.underline('World!'))

    def test_init(self):
        swf = StringWithFormatting('Hello')
        self.assertEqual(swf._content, (NullComponentSpec('Hello'),))
        swf = StringWithFormatting(swf)
        self.assertEqual(swf._content, (NullComponentSpec('Hello'),))
        swf = StringWithFormatting(NullComponentSpec('World'))
        self.assertEqual(swf._content, (NullComponentSpec('World'),))
        swf = StringWithFormatting((NullComponentSpec('Bob'),))
        self.assertEqual(swf._content, (NullComponentSpec('Bob'),))
        content = (NullComponentSpec('one'), StringComponentSpec(None, 'two'))
        swf = StringWithFormatting(content)
        self.assertEqual(swf._content, content)
        swf = StringWithFormatting(
            (NullComponentSpec('All '), NullComponentSpec('Together')))
        self.assertEqual(swf._content, (NullComponentSpec('All Together'),))

    def test_len(self):
        self.assertEqual(len(self.swf), len('Hello World!'))

    def test_str(self):
        self.assertEqual(str(self.swf), 'Hello World!')

    def test_getitem_index(self):
        self.assertEqual(self.swf[2], 'l')
        self.assertEqual(self.swf[7], 'o')

    def test_getitem_slice(self):
        self.assertEqual(self.swf[:], self.swf)
        expected = 'lo ' + self.format.blue(self.format.underline('World!'))
        self.assertEqual(self.swf[3:], expected)
        self.assertEqual(self.swf[3:100], expected)
        self.assertEqual(self.swf[3:len(self.swf)], expected)
        expected = 'o ' + self.format.blue(self.format.underline('Wor'))
        self.assertEqual(self.swf[4:9], expected)
        expected = StringWithFormatting('llo')
        self.assertEqual(self.swf[2:5], expected)
        expected = StringWithFormatting('llo ')
        self.assertEqual(self.swf[2:6], expected)
        expected = 'Hello ' + self.format.blue(self.format.underline('Wo'))
        self.assertEqual(self.swf[:8], expected)
        expected = StringWithFormatting(
            self.format.blue(self.format.underline('World')))
        self.assertEqual(self.swf[6:11], expected)
        expected = StringWithFormatting(
            self.format.blue(self.format.underline('orld!')))
        self.assertEqual(self.swf[7:12], expected)

    def test_end_to_end(self):
        terminal = Terminal(force_styling=True)
        terminal.stream = StringIO()
        text = Text(self.swf)
        text.draw(6, 2, terminal=terminal)
        result = terminal.stream.getvalue()
        # FIXME: 'Hello ' in the expected result below shouldn't have a
        # trailing space in it, because the word wrapping initiated by Text
        # should have stripped it off.
        expected = (
            terminal.move(0, 0) + 'Hello ' + terminal.move(1, 0) +
            terminal.blue + terminal.underline + 'World!' + terminal.normal +
            terminal.blue + terminal.normal)
        self.assertEqual(repr(result), repr(expected))


class TestTextWrapper(TestCase):
    def setUp(self):
        self.format = FormatSpecFactory()

    def test_wrap_str(self):
        text = 'The  quick brown fox jumps over the lazy dog'
        result = wrap(text, width=15)
        expected = [
            'The  quick',
            'brown fox jumps',
            'over the lazy',
            'dog']
        self.assertEqual(result, expected)
        self.assertEqual(wrap('', 10), [])

    def test_wrap_str_with_formatting(self):
        long_swf = (
            '  This  is a    rather ' + self.format.bold('loooong ') +
            'string th' + self.format.green('at needs wrapppppp') + 'ing ')
        result = wrap(long_swf, width=11)
        expected = [
            StringWithFormatting('This  is a'),
            StringWithFormatting('rather'),
            StringWithFormatting(self.format.bold('loooong')),
            'string th' + self.format.green('at'),
            StringWithFormatting(self.format.green('needs wrapp')),
            self.format.green('pppp') + 'ing']
        self.assertEqual(result, expected)
