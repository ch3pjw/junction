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
from mock import Mock

from jcn.input_elements import LineBuffer, LineInput
from jcn.terminal import Terminal


class TestInputElements(TestCase):
    def test_line_buffer(self):
        self.line_buffer = LineBuffer()
        self.assertFalse(self.line_buffer)
        self._buffer_input_helper('hello world', 'hello world')
        self.assertTrue(self.line_buffer)
        self.assertEqual(len(self.line_buffer), len('hello world'))
        self._buffer_input_helper(['backspace', 'backspace'], 'hello wor')
        self._buffer_input_helper(['delete'], 'hello wor')
        self._buffer_input_helper(['left', 'left', 'backspace'], 'hello or')
        self._buffer_input_helper(['delete'], 'hello r')
        self._buffer_input_helper(['end', 'backspace', 'backspace'], 'hello')
        self._buffer_input_helper(['home', 'delete'], 'ello')
        self._buffer_input_helper(['backspace'], 'ello')
        self._buffer_input_helper('H', 'Hello')
        self._buffer_input_helper(
            ['right'] * 5 + ['space'] + list('World'), 'Hello World')
        self._buffer_input_helper(
            ['left'] * 5 + list('Successful') + ['space'],
            'Hello Successful World')
        self.line_buffer.clear()
        self.assertEqual(str(self.line_buffer), '')

    def _buffer_input_helper(self, sequence, expected_result):
        for char in sequence:
            self.line_buffer.handle_input(char)
        self.assertEqual(str(self.line_buffer), expected_result)

    def test_line_input(self):
        terminal = Terminal(force_styling=True)
        line_input = LineInput('placeholder text')
        line_input.root = Mock()
        block = line_input._get_lines(0, 0)
        self.assertEqual(block, ['placeholder text'])
        for char in 'some important input':
            line_input.handle_input(char)
        block = line_input._get_lines(0, 0)
        self.assertEqual(
            block, ['some important input' + terminal.reverse(' ')])
