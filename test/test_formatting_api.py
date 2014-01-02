# Copyright (C) 2013 Paul Weaver <p.weaver@ruthorn.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

from unittest import TestCase
from io import StringIO

from jcn.formatting import (
    EscapeSequenceStack, StringComponentSpec, NullComponentSpec,
    FormatPlaceholder, ParamaterizingFormatPlaceholder, StylePlaceholder,
    FormatPlaceholderFactory, StylePlaceholderFactory, StringWithFormatting)
from jcn import Terminal, Text, Fill


class TestStringComponentSpec(TestCase):
    def setUp(self):
        class TestClass(StringComponentSpec):
            def _populate(self):
                pass
        self.test_cls = TestClass

    def test_len(self):
        self.assertEqual(len(self.test_cls('blue', 'content')), 7)

    def test_str(self):
        self.assertEqual(str(self.test_cls('blue', 'content')), 'content')

    def test_repr(self):
        self.assertEqual(
            repr(self.test_cls('green', 'beret')),
            "TestClass('green', 'beret')")

    def test_getattr(self):
        spec = self.test_cls('bold', '  Hello!  ')
        self.assertEqual(spec.strip(), self.test_cls('bold', 'Hello!'))


class TestParameterizingFormatPlaceholder(TestCase):
    def setUp(self):
        self.terminal = Terminal(force_styling=True)
        self.factory = FormatPlaceholderFactory()
        self.stack = EscapeSequenceStack(self.terminal.normal)

    def test_too_many_calls(self):
        param_fmt_placeholder = self.factory.color(230)
        with self.assertRaises(TypeError):
            param_fmt_placeholder('user content')('extra call')

    def test_populate(self):
        param_fmt_placeholder = self.factory.color
        with self.assertRaises(ValueError):
            param_fmt_placeholder.populate(self.terminal, {})
        result = param_fmt_placeholder(121)
        self.assertIsInstance(result, ParamaterizingFormatPlaceholder)
        result = param_fmt_placeholder.populate(self.terminal, {})
        self.assertEqual(repr(result), repr(self.terminal.color(121)))
        spec = param_fmt_placeholder('important info')
        # FIXME: it might be nicer if the stack was something that existed on
        # the Terminal...
        result = spec.populate(self.terminal, {}, self.stack)
        self.assertEqual(repr(result), repr(
            self.terminal.color(121) + 'important info' +
            self.terminal.normal))


class TestNullComponent(TestCase):
    def test_equal(self):
        self.assertEqual(
            NullComponentSpec('hello'), NullComponentSpec('hello'))
        self.assertNotEqual(
            NullComponentSpec('hello'), NullComponentSpec('world'))


class TestPlaceholder(TestCase):
    def setUp(self):
        self.terminal = Terminal(force_styling=True)
        self.format = FormatPlaceholderFactory()
        self.style = StylePlaceholderFactory()
        self.styles = {
            'heading': self.format.underline,
            'h1': self.style.heading,
            'h2': self.style.heading + self.format.red}

    def test_eq(self):
        self.assertEqual(FormatPlaceholder('red'), FormatPlaceholder('red'))
        self.assertNotEqual(
            FormatPlaceholder('red'), FormatPlaceholder('green'))
        self.assertNotEqual(
            FormatPlaceholder('blue'), StylePlaceholder('blue'))

    def test_repr(self):
        self.assertEqual(
            repr(FormatPlaceholder('red')), "FormatPlaceholder('red')")

    def test_populate_format_placeholder(self):
        format_placeholder = FormatPlaceholder('red')
        result = format_placeholder.populate(self.terminal, self.styles)
        self.assertEqual(result, self.terminal.red)

    def test_populate_style_placeholder_simple(self):
        style_placeholder = StylePlaceholder('heading')
        result = style_placeholder.populate(self.terminal, self.styles)
        self.assertEqual(result, self.terminal.underline)

    def test_populate_style_placeholder_style_ref(self):
        style_placeholder = StylePlaceholder('h1')
        result = style_placeholder.populate(self.terminal, self.styles)
        self.assertEqual(result, self.terminal.underline)

    def test_populate_style_placeholder_compound(self):
        style_placeholder = StylePlaceholder('h2')
        result = style_placeholder.populate(self.terminal, self.styles)
        self.assertEqual(result, self.terminal.underline + self.terminal.red)

    def test_bad_addition(self):
        with self.assertRaises(TypeError):
            self.format.yellow + 'fail'


class TestStringWithFormatting(TestCase):
    def setUp(self):
        self.format = FormatPlaceholderFactory()
        self.style = StylePlaceholderFactory()
        self.swf = 'Hello ' + self.format.blue(self.format.underline('World!'))
        self.terminal = Terminal(force_styling=True)

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
        self.assertEqual(swf._content, (NullComponentSpec('onetwo'),))
        content = (
            NullComponentSpec('one'), StringComponentSpec('foo', 'two'))
        swf = StringWithFormatting(content)
        self.assertEqual(swf._content, content)
        swf = StringWithFormatting(
            (NullComponentSpec('All '), NullComponentSpec('Together')))
        self.assertEqual(swf._content, (NullComponentSpec('All Together'),))

    def test_len(self):
        self.assertEqual(len(self.swf), len('Hello World!'))

    def test_str(self):
        self.assertEqual(str(self.swf), 'Hello World!')

    def test_contains(self):
        self.assertIn('lo', self.swf)

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

    def test_splitlines(self):
        swf = self.format.red('hello\nworld') + '\ntea'
        expected = [
            StringWithFormatting(self.format.red('hello')),
            StringWithFormatting(self.format.red('world')),
            StringWithFormatting('tea')]
        self.assertEqual(swf.splitlines(), expected)

    def test_nested_formats(self):
        swf = self.format.bold('hello ') + self.format.reverse(
            self.format.green('wor') + 'ld')
        expected = (
            self.terminal.bold + 'hello ' + self.terminal.normal +
            self.terminal.reverse + self.terminal.green + 'wor' +
            self.terminal.normal + self.terminal.reverse + 'ld' +
            self.terminal.normal)
        esc_seq_stack = EscapeSequenceStack(self.terminal.normal)
        result = swf.populate(self.terminal, self.style, esc_seq_stack)
        self.assertEqual(repr(result), repr(expected))

    def test_end_to_end(self):
        self.terminal.stream = StringIO()
        text = Text(self.swf)
        text.draw(6, 2, terminal=self.terminal)
        result = self.terminal.stream.getvalue()
        expected = (
            self.terminal.normal + self.terminal.move(0, 0) + 'Hello ' +
            self.terminal.move(1, 0) + self.terminal.blue +
            self.terminal.underline + 'World!' + self.terminal.normal +
            self.terminal.blue + self.terminal.normal)
        self.assertEqual(repr(result), repr(expected))
        self.terminal.stream = StringIO()
        text.content = 'Plainly formatted info'
        text.update(terminal=self.terminal)
        result = self.terminal.stream.getvalue()
        expected = (
            self.terminal.normal + self.terminal.move(0, 0) + 'Plainl' +
            self.terminal.move(1, 0) + 'y form')
        self.assertEqual(repr(result), repr(expected))


class TestDefaultFormatting(TestCase):
    def setUp(self):
        self.terminal = Terminal(stream=StringIO(), force_styling=True)
        self.format = FormatPlaceholderFactory()

    def test_simple_default_formatting(self):
        fill = Fill()
        fill.default_format = (
            self.format.bold + self.format.green + self.format.underline)
        fill.draw(3, 1, terminal=self.terminal)
        result = self.terminal.stream.getvalue()
        expected = (
            self.terminal.normal + self.terminal.bold + self.terminal.green +
            self.terminal.underline + self.terminal.move(0, 0) + '...' +
            self.terminal.normal)
        self.assertEqual(repr(result), repr(expected))

    def test_default_formatting_with_other_formatting(self):
        text = Text(self.format.underline('content'))
        text.default_format = self.format.blue
        text.draw(7, 1, terminal=self.terminal)
        result = self.terminal.stream.getvalue()
        expected = (
            self.terminal.normal + self.terminal.blue +
            self.terminal.move(0, 0) + self.terminal.underline + 'content' +
            self.terminal.normal + self.terminal.blue + self.terminal.normal)
        self.assertEqual(repr(result), repr(expected))
