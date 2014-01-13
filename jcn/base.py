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

from abc import ABCMeta, abstractmethod
from collections import namedtuple

from .terminal import get_terminal
from .formatting import (
    StringWithFormatting, FormatPlaceholder, PlaceholderGroup)


Geometry = namedtuple(
    'Geometry', ['width', 'height', 'x', 'y', 'x_crop', 'y_crop'])


class Block:
    __slots__ = 'x', 'y', 'lines', 'default_format'

    def __init__(self, x, y, lines, default_format):
        self.x = x
        self.y = y
        self.lines = lines
        self.default_format = default_format

    def __repr__(self):
        args = [self.x, self.y, self.lines]
        if self.default_format:
            args.append(self.default_format)
        return '{}({})'.format(
            self.__class__.__name__, ', '.join(repr(arg) for arg in args))

    def __eq__(self, other):
        try:
            return all(
                getattr(self, attr_name) == getattr(other, attr_name) for
                attr_name in self.__slots__)
        except AttributeError:
            return False

    def __iter__(self):
        return iter(self.lines)


class ABCUIElement(metaclass=ABCMeta):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    _all_valigns = 'top', 'middle', 'bottom'
    _possible_valigns = _all_valigns
    _all_haligns = 'left', 'center', 'right'
    _possible_haligns = _all_haligns

    def __init__(self, halign='left', valign='top', fillchar=' ', name=''):
        self._halign = None
        self._valign = None
        self.halign = halign
        self.valign = valign
        self.fillchar = fillchar
        self.name = name
        self.updated = True
        self._previous_geometry = None
        self._default_format = None
        self.root = None

    def __repr__(self):
        if self.name:
            return '<{} element {!r}>'.format(
                self.__class__.__name__, self.name)
        else:
            return '<{} element at {}>'.format(
                self.__class__.__name__, hex(id(self)))

    def _set_align(self, orientation, value):
        '''We define a setter because it's better to diagnose this kind of
        programmatic error here than have to work out why alignment is odd when
        we sliently fail!
        '''
        orientation_letter = orientation[0]
        possible_alignments = getattr(
            self, '_possible_{}aligns'.format(orientation_letter))
        all_alignments = getattr(
            self, '_all_{}aligns'.format(orientation_letter))
        if value not in possible_alignments:
            if value in all_alignments:
                msg = 'non-permitted'
            else:
                msg = 'non-existant'
            raise ValueError(
                "Can't set {} {} alignment {!r} on element {!r}".format(
                    msg, orientation, value, self))
        setattr(self, '_{}align'.format(orientation_letter), value)

    @property
    def halign(self):
        return self._halign

    @halign.setter
    def halign(self, value):
        self._set_align('horizontal', value)
        self.updated = True

    @property
    def valign(self):
        return self._valign

    @valign.setter
    def valign(self, value):
        self._set_align('vertical', value)
        self.updated = True

    def get_min_size(self, dimension):
        if dimension == 'width':
            return self.min_width
        else:
            return self.min_height

    def get_max_size(self, dimension):
        if dimension == 'width':
            return self.max_width
        else:
            return self.max_height

    @property
    def default_format(self):
        return self._default_format

    @default_format.setter
    def default_format(self, value):
        self._default_format = value
        self.updated = True

    def draw(self, width, height, x=0, y=0, x_crop='left', y_crop='top',
             terminal=None, styles=None):
        blocks = self.get_all_blocks(width, height, x, y, x_crop, y_crop)
        self._do_draw(blocks, terminal, styles)

    def update(self, default_format=None, terminal=None, styles=None):
        blocks = self.get_updated_blocks(default_format)
        self._do_draw(blocks, terminal, styles)

    def _do_draw(self, blocks, terminal, styles):
        terminal = terminal or get_terminal()
        styles = styles or {}
        for block in blocks:
            if block.default_format:
                default_esq_seq = (
                    terminal.normal + block.default_format.populate(
                        terminal, styles))
            else:
                default_esq_seq = terminal.normal
            lines = self._populate_lines(
                block, terminal, styles, default_esq_seq)
            terminal.draw_lines(lines, block.x, block.y)
        terminal.stream.flush()

    def _populate_lines(self, block, terminal, styles, default_esc_seq):
        '''Takes some lines to draw to the terminal, which may contain
        formatting placeholder objects, and inserts the appropriate concrete
        escapes sequences by using data from the terminal object and styles
        dictionary.
        '''
        for line in block:
            if hasattr(line, 'populate'):
                line = line.populate(terminal, styles, default_esc_seq)
            else:
                line = default_esc_seq + line
            yield line

    def get_all_blocks(
            self, width, height, x=0, y=0, x_crop='left', y_crop='top',
            default_format=None):
        if self.default_format:
            if default_format:
                default_format = default_format + self.default_format
            else:
                default_format = self.default_format
        blocks = self._get_all_blocks(
            width, height, x, y, x_crop, y_crop, default_format)
        self._previous_geometry = Geometry(width, height, x, y, x_crop, y_crop)
        self.updated = False
        return blocks

    @abstractmethod
    def _get_all_blocks(
            self, width, height, x, y, x_crop, y_crop, default_format):
        pass

    def get_updated_blocks(self, default_format=None):
        if self._previous_geometry is None:
            raise ValueError("draw() must be called on {!r} before it can be "
                             "updated".format(self))
        if self.default_format:
            if default_format:
                default_format = default_format + self.default_format
            else:
                default_format = self.default_format
        blocks = []
        if self.updated:
            blocks.extend(self._get_updated_blocks(default_format))
            self.updated = False
        return blocks

    @abstractmethod
    def _get_updated_blocks(self, default_format):
        pass

    #@abstractmethod
    def handle_input(self, data):
        #print('{!r} got {!r}'.format(self, data))
        return data
