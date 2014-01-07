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

from abc import abstractmethod

from .base import ABCUIElement, Block
from .util import clamp, crop_or_expand
from .textwrap import wrap


class ABCDisplayElement(ABCUIElement):
    _schemes = {
        'left': 'beginning',
        'center': 'middle',
        'right': 'end',
        'top': 'beginning',
        'middle': 'middle',
        'bottom': 'end'}

    def _get_updated_blocks(self, default_format):
        return self._get_all_blocks(
            *self._previous_geometry,
            default_format=default_format)

    @abstractmethod
    def _get_lines(self, width, height):
        '''Returns a list of individual lines that make up the display of the
        UI element.
        '''

    def _do_crop(self, lines, width, height, x_crop, y_crop):
        '''Crops a list of strings to the specified width/height
        '''
        lines = crop_or_expand(
            lines, height, default=[self.fillchar * width],
            scheme=self._schemes[y_crop])
        for i, line in enumerate(lines):
            lines[i] = crop_or_expand(
                line, width, default=self.fillchar,
                scheme=self._schemes[x_crop])
        return lines

    def _get_all_blocks(
            self, width, height, x, y, x_crop, y_crop, default_format):
        full_width = clamp(width, min_=self.min_width, max_=self.max_width)
        full_height = clamp(height, min_=self.min_height, max_=self.max_height)
        lines = self._get_lines(full_width, full_height)
        lines = self._do_crop(
            lines, full_width, full_height, self._halign, self._valign)
        # Perform an additional crop with *different alignment* to resize the
        # UI element's rendered area text to the required area:
        lines = self._do_crop(lines, width, height, x_crop, y_crop)
        return [Block(x, y, lines, default_format)]


class Fill(ABCDisplayElement):
    def __init__(self, char='.', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char = char

    def _get_lines(self, width, height):
        return [self.char * width] * height


class Text(ABCDisplayElement):
    def __init__(self, content='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = content

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value
        self.updated = True
        if self.root:
            self.root.update()

    def _get_lines(self, width, height):
        unwrapped_lines = self.content.splitlines()
        result = []
        for line in unwrapped_lines:
            result.extend(wrap(line, width))
        return result


class Label(Text):
    min_height = max_height = 1

    def _get_lines(self, width, height):
        return [self.content]


class ProgressBar(ABCDisplayElement):
    min_width = 3
    min_height = 1
    max_height = 1

    def __init__(self, chars=None):
        super().__init__()
        if not chars or len(chars) < 4:
            chars = '[ -=]'
        self._start_cap = chars[0]
        self._end_cap = chars[-1]
        self._bg_char = chars[1]
        self._progress_chars = chars[2:-1]
        self._fraction = 0

    @property
    def fraction(self):
        return self._fraction

    @fraction.setter
    def fraction(self, value):
        self._fraction = clamp(value, 0, 1)
        self.updated = True
        if self.root:
            self.root.update()

    def _get_lines(self, width, height):
        width = max(width, self.min_width) - 2
        chars = [self._bg_char] * width
        filled = self._fraction * width
        over = filled - int(filled)
        filled = int(filled)
        chars[:filled] = self._progress_chars[-1] * filled
        if over:
            final_char = self._progress_chars[
                int(over * len(self._progress_chars))]
            chars[filled] = final_char
        return ['{}{}{}'.format(
            self._start_cap, ''.join(chars), self._end_cap)]
