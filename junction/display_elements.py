from abc import abstractmethod

from .base import ABCUIElement, Block
from .root import Root
from .util import clamp, crop_or_expand
from .formatting import StringWithFormatting, wrap


class ABCDisplayElement(ABCUIElement):
    _scheme = {
        'left': 'beginning',
        'center': 'middle',
        'right': 'end',
        'top': 'beginning',
        'middle': 'middle',
        'bottom': 'end'}

    def _get_updated_blocks(self, default_format):
        return self.get_all_blocks(
            *self._previous_geometry,
            default_format=self.default_format or default_format)

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
            scheme=self._scheme[y_crop])
        for i, line in enumerate(lines):
            lines[i] = crop_or_expand(
                line, width, default=self.fillchar,
                scheme=self._scheme[x_crop])
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
        return [Block(x, y, lines, self.default_format or default_format)]


class Fill(ABCDisplayElement):
    def __init__(self, char='.', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char = char

    def _get_lines(self, width, height):
        return [self.char * width] * height


class Label(ABCDisplayElement):
    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def _get_lines(self, width, height):
        return [self.content]


class Text(ABCDisplayElement):
    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = content

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    def _get_lines(self, width, height):
        lines = wrap(self.content, width)
        if any(isinstance(line, StringWithFormatting) for line in lines):
            lines[-1] += Root.format.normal
        return lines


class ProgressBar(ABCDisplayElement):
    min_width = 3
    min_height = 1
    max_height = 1

    def __init__(self, chars=None):
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
