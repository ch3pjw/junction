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

from .util import clamp
from .display_elements import ABCDisplayElement, Text
from .terminal import get_terminal


class LineBuffer:
    # Yes, the irony of re-implementing a bunch of stuff we've gone out of way
    # to turn off in the terminal is not lost on me ;-)
    def __init__(self):
        self.content = ''
        self.cursor_position = 0
        self.line_received_callback = None

    def __bool__(self):
        return bool(self.content)

    def __len__(self):
        return len(self.content)

    def __str__(self):
        return self.content

    def draw(self):
        # FIXME: Might want to reconsider how we do formatting so that the
        # cursor style doesn't end up being hard-coded here...
        terminal = get_terminal()
        if self.cursor_position == len(self.content):
            return self.content + terminal.reverse(' ')
        else:
            return (
                self.content[:self.cursor_position] +
                terminal.reverse(self.content[self.cursor_position]) +
                self.content[self.cursor_position + 1:])

    def clear(self):
        self.content = ''
        self.cursor_position = 0

    def handle_input(self, data):
        if len(data) == 1:
            self._insert_char(data)
        elif data == 'space':
            self._insert_char(' ')
        elif data == 'backspace':
            self._backspace_char()
        elif data == 'delete':
            self._delete_char(self.cursor_position)
        elif data == 'left':
            self._move_cursor(-1)
        elif data == 'right':
            self._move_cursor(1)
        elif data == 'home':
            self.cursor_position = 0
        elif data == 'end':
            self.cursor_position = len(self.content)
        elif data == 'return':
            self._line_received()

    def _insert_char(self, char):
        pos = self.cursor_position
        if pos == len(self.content):
            self.content += char
        else:
            self.content = self.content[:pos] + char + self.content[pos:]
        self.cursor_position += 1

    def _backspace_char(self):
        if self.cursor_position == 0:
            return
        if self.cursor_position == len(self.content):
            self.content = self.content[:-1]
        else:
            self._delete_char(self.cursor_position - 1)
        self.cursor_position -= 1

    def _delete_char(self, pos):
        self.content = self.content[:pos] + self.content[pos + 1:]

    def _move_cursor(self, delta):
        self.cursor_position = clamp(
            self.cursor_position + delta, min_=0, max_=len(self))

    def _line_received(self):
        if self.line_received_callback:
            self.line_received_callback(self.content)
        self.clear()


class Input(Text):
    # I'm not sure I'm liking the constraints that the interrelationship of
    # Text and Input imposes...
    def __init__(self, placeholder_text, *args, **kwargs):
        super().__init__(content=LineBuffer(), *args, **kwargs)
        self.placeholder_text = placeholder_text

    @property
    def content(self):
        if self._content:
            return str(self._content)
        else:
            return self.placeholder_text

    @content.setter
    def content(self, value):
        self._content.content = value

    def handle_input(self, data):
        self._content.handle_input(data)
        # FIXME: this is a temporary hack to try proof of concept
        self.root.draw()


class LineInput(ABCDisplayElement):
    def __init__(self, placeholder_text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.placeholder_text = placeholder_text
        self.line_buffer = LineBuffer()

    def handle_input(self, data):
        self.line_buffer.handle_input(data)
        self.updated = True
        # FIXME: this is a temporary hack to try proof of concept
        self.root.update()

    def _get_lines(self, width, height):
        if self.line_buffer:
            return [self.line_buffer.draw()]
        else:
            return [self.placeholder_text]
