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
from mock import patch

from jcn.formatting import (
    StringComponent, FormatPlaceholder,
    ParameterizingFormatPlaceholder, PlaceholderGroup, StylePlaceholder,
    null_placeholder, FormatPlaceholderFactory, StylePlaceholderFactory,
    StringWithFormatting)
from jcn.textwrap import _TextWrapper
from jcn import Terminal, Text, Fill


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

    def test_call(self):
        placeholder = FormatPlaceholder('black')
        result = placeholder('test')
        expected = StringComponent(placeholder, 'test')
        self.assertEqual(result, expected)
        result = placeholder(StringComponent(
            FormatPlaceholder('white'), 'test'))
        expected = StringComponent(
            PlaceholderGroup([FormatPlaceholder('white'), placeholder]),
            'test')
        self.assertEqual(result, expected)
        result = placeholder(StringWithFormatting((
            StringComponent(FormatPlaceholder('bold'), 'hello '),
            StringComponent(FormatPlaceholder('underline'), 'world'))))
        expected = StringWithFormatting((
            StringComponent(
                PlaceholderGroup(
                    [FormatPlaceholder('bold'), placeholder]),
                'hello '),
            StringComponent(
                PlaceholderGroup(
                    [FormatPlaceholder('underline'), placeholder]),
                'world')))
        self.assertEqual(result, expected)

    def test_bad_addition(self):
        with self.assertRaises(TypeError):
            self.format.yellow + 'fail'


class TestParameterizingFormatPlaceholder(TestCase):
    def setUp(self):
        self.terminal = Terminal(force_styling=True)
        self.factory = FormatPlaceholderFactory()

    def test_too_many_calls(self):
        param_fmt_placeholder = self.factory.color(230)
        with self.assertRaises(TypeError):
            param_fmt_placeholder('user content')('extra call')

    def test_populate(self):
        param_fmt_placeholder = self.factory.color
        with self.assertRaises(ValueError):
            param_fmt_placeholder.populate(self.terminal, {})
        result = param_fmt_placeholder(121)
        self.assertIsInstance(result, ParameterizingFormatPlaceholder)
        result = param_fmt_placeholder.populate(self.terminal, {})
        self.assertEqual(repr(result), repr(self.terminal.color(121)))
        component = param_fmt_placeholder('important info')
        result = component.populate(self.terminal, {}, self.terminal.normal)
        expected = (
            self.terminal.normal + self.terminal.color(121) + 'important info')
        self.assertEqual(repr(result), repr(expected))


class TestStringComponent(TestCase):
    def test_basic(self):
        s = StringComponent('blue', 'hello world')
        self.assertEqual(str(s), 'hello world')
        self.assertEqual(s.placeholder, 'blue')

    def test_repr(self):
        placeholder = FormatPlaceholder('tangerine')
        s = StringComponent(placeholder, 'melons')
        self.assertIn(repr(placeholder), repr(s))
        self.assertIn(repr('melons'), repr(s))

    def test_eq(self):
        s = StringComponent('yellow', 'hello world')
        self.assertNotEqual(s, 'hello world')
        self.assertNotEqual(
            s, StringComponent(null_placeholder, 'hello world'))
        self.assertNotEqual(s, StringComponent('yellow', 'not hello world'))
        self.assertEqual(s, StringComponent('yellow', 'hello world'))
        s = StringComponent(null_placeholder, 'plain')
        self.assertEqual(s, 'plain')
        self.assertEqual(s, StringComponent(null_placeholder, 'plain'))

    def test_getitem(self):
        s = StringComponent('red', 'bob')
        self.assertEqual(s[1], StringComponent('red', 'o'))
        self.assertEqual(s[:], StringComponent('red', 'bob'))

    def test_split(self):
        s = StringComponent('blue', 'hello world')
        result = s.split()
        expected = [
            StringComponent('blue', 'hello'),
            StringComponent('blue', 'world')]
        self.assertEqual(result, expected)
        # Exercise cache of string method
        result = s.split()
        self.assertEqual(result, expected)

    def test_strip(self):
        s = StringComponent('purple', ' spaced-out  world  ')
        result = s.strip()
        expected = StringComponent('purple', 'spaced-out  world')
        self.assertEqual(result, expected)

    def test_add_str(self):
        s = StringComponent(null_placeholder, 'boring')
        result = s + ' old string'
        expected = StringComponent(null_placeholder, 'boring old string')
        self.assertEqual(result, expected)
        s = StringComponent(FormatPlaceholder('red'), 'wow')
        result = s + ' exciting colour'
        expected = StringWithFormatting(
            (s, StringComponent(null_placeholder, ' exciting colour')))
        self.assertEqual(result, expected)

    def test_add_string_component(self):
        s1 = StringComponent('a', 'hello')
        s2 = StringComponent('b', 'world')
        result = s1 + s2
        expected = StringWithFormatting((
            StringComponent('a', 'hello'),
            StringComponent('b', 'world')))
        self.assertEqual(result, expected)

    def test_populate(self):
        terminal = Terminal(force_styling=True)
        s = StringComponent(FormatPlaceholder('red'), 'angry!')
        result = s.populate(terminal, {}, terminal.normal)
        expected = terminal.normal + terminal.red + 'angry!'
        self.assertEqual(repr(result), repr(expected))


class TestStringWithFormatting(TestCase):
    def setUp(self):
        self.format = FormatPlaceholderFactory()
        self.style = StylePlaceholderFactory()
        self.swf = 'Hello ' + self.format.blue(self.format.underline('World!'))
        self.terminal = Terminal(force_styling=True)

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


class NewTestStringWithFormatting(TestCase):
    def setUp(self):
        self.format = FormatPlaceholderFactory()
        self.style = StylePlaceholderFactory()
        self.terminal = Terminal(force_styling=True)

    def test_init(self):
        swf = StringWithFormatting('Hello')
        self.assertEqual(
            swf._content, (StringComponent(null_placeholder, 'Hello'),))
        swf = StringWithFormatting(swf)
        self.assertEqual(
            swf._content, (StringComponent(null_placeholder, 'Hello'),))
        swf = StringWithFormatting(StringComponent(null_placeholder, 'World'))
        self.assertEqual(
            swf._content, (StringComponent(null_placeholder, 'World'),))
        swf = StringWithFormatting((StringComponent(null_placeholder, 'Bob'),))
        self.assertEqual(
            swf._content, (StringComponent(null_placeholder, 'Bob'),))
        content = (
            StringComponent(
                null_placeholder, 'one'), StringComponent('foo', 'two'))
        swf = StringWithFormatting(content)
        self.assertEqual(swf._content, content)

    def test_len(self):
        s = StringWithFormatting(('hello'))
        self.assertEqual(len(s), len('hello'))
        s = StringComponent('blue', 'hello ') + StringComponent('red', 'world')
        self.assertIsInstance(s, StringWithFormatting)
        self.assertEqual(len(s), len('hello world'))

    def test_str(self):
        s = StringWithFormatting('I love cheese')
        self.assertEqual(str(s), 'I love cheese')
        s = 'I love ' + self.format.yellow('cheese')
        self.assertEqual(str(s), 'I love cheese')

    def test_contains(self):
        s = 'Perhaps ' + self.format.red('chocolate')
        self.assertIn('aps choc', s)

    def test_getitem_index(self):
        s = self.format.underline('Linux') + ' rulz ok'
        for i, c in enumerate('Linux rulz ok'):
            self.assertEqual(s[i], c)
        self.assertEqual(s[-1], 'k')
        with self.assertRaises(IndexError):
            s[121]

    def test_getitem_slice(self):
        swf = 'Hello ' + self.format.blue(self.format.underline('World!'))
        self.assertEqual(swf[:], swf)
        expected = 'lo ' + self.format.blue(self.format.underline('World!'))
        self.assertEqual(swf[3:], expected)
        self.assertEqual(swf[3:100], expected)
        self.assertEqual(swf[3:len(swf)], expected)
        expected = 'o ' + self.format.blue(self.format.underline('Wor'))
        print(repr(swf[4:9]))
        print('-' * 20)
        print(repr(expected))
        self.assertEqual(swf[4:9], expected)
        expected = StringWithFormatting('llo')
        self.assertEqual(swf[2:5], expected)
        expected = StringWithFormatting('llo ')
        self.assertEqual(swf[2:6], expected)
        expected = 'Hello ' + self.format.blue(self.format.underline('Wo'))
        self.assertEqual(swf[:8], expected)
        expected = StringWithFormatting(
            self.format.blue(self.format.underline('World')))
        self.assertEqual(swf[6:11], expected)
        expected = StringWithFormatting(
            self.format.blue(self.format.underline('orld!')))
        self.assertEqual(swf[7:12], expected)

    def test_chunk_simple(self):
        s = StringWithFormatting('This is some text')
        result = s.chunk(_TextWrapper.wordsep_re)
        expected = [
            StringWithFormatting(StringComponent(null_placeholder, chunk)) for
            chunk in ['This', ' ', 'is', ' ', 'some', ' ', 'text']]
        self.assertEqual(result, expected)

    def test_chunk_with_formatting(self):
        content = (
            StringComponent('blue', 'This is so'),
            StringComponent('red', 'me text'))
        s = StringWithFormatting(content)
        result = s.chunk(_TextWrapper.wordsep_re)
        expected = [
            StringWithFormatting(StringComponent('blue', 'This')),
            StringWithFormatting(StringComponent('blue', ' ')),
            StringWithFormatting(StringComponent('blue', 'is')),
            StringWithFormatting(StringComponent('blue', ' ')),
            StringWithFormatting((
                StringComponent('blue', 'so'),
                StringComponent('red', 'me'))),
            StringWithFormatting(StringComponent('red', ' ')),
            StringWithFormatting(StringComponent('red', 'text'))]
        self.assertEqual(result, expected)

    def test_splitlines(self):
        swf = self.format.red('hello\nworld') + '\ntea'
        result = swf.splitlines()
        expected = [
            StringWithFormatting(self.format.red('hello')),
            StringWithFormatting(self.format.red('world')),
            StringWithFormatting('tea')]
        self.assertEqual(result, expected)

    def test_strip(self):
        s = StringWithFormatting((
            StringComponent('green', '  hello world '),))
        result = s.strip()
        expected = StringWithFormatting((
            StringComponent('green', 'hello world'),))
        self.assertEqual(result, expected)
        s = StringWithFormatting((
            StringComponent('blue', ' hello '),
            StringComponent('red', 'world ')))
        result = s.strip()
        expected = StringWithFormatting((
            StringComponent('blue', 'hello '),
            StringComponent('red', 'world')))
        self.assertEqual(result, expected)

    def test_nested_formats(self):
        swf = self.format.bold('hello ') + self.format.reverse(
            self.format.green('wor') + 'ld')
        expected = (
            self.terminal.normal + self.terminal.bold + 'hello ' +
            self.terminal.normal + self.terminal.green + self.terminal.reverse
            + 'wor' + self.terminal.normal + self.terminal.reverse + 'ld')
        result = swf.populate(self.terminal, self.style)
        self.assertEqual(repr(result), repr(expected))

    @patch('jcn.formatting.get_terminal')
    def test_populate_with_no_args(self, mock_get_terminal):
        mock_get_terminal.return_value = self.terminal
        swf = 'Hello ' + self.format.blue(self.format.underline('World!'))
        result = swf.populate()
        expected = (
            self.terminal.normal + 'Hello ' + self.terminal.normal +
            self.terminal.underline + self.terminal.blue + 'World!')
        self.assertIsInstance(result, str)
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
