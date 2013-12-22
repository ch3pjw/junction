from abc import abstractmethod

from .base import ABCUIElement
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

    def _draw(self, width, height, x, y, x_crop, y_crop, default_format,
              terminal):
        '''Instuct the UI element to draw itself to the terminal.

        :parameter width: The width that the element must take up on the screen
            (if the underlying code failes to provide the correctly sized data,
            we will take measures to adjust it).
        :parameter height: The height that the element must take up on the
            screen.
        :parameter x: an optional x location at which to draw the UI element,
            default=0.
        :parameter y: an optional y location at which to draw the UI element,
            default=0.
        :parameter x_crop: If width < min_width, the alignment that will be
            used to crop the element to the right size (if None is specified,
            default, we will use this element's halign).
        :parameter y_crop: If height < min_height, the alignment that will be
            uese to crop the element to the right size (if None is specified,
            default, we will use this element's valign).
        '''
        block = self._get_cropped_block(width, height)
        # Perform an additional crop with *different alignment* to resize the
        # UI element's rendered area text to the required area:
        block = self._do_crop(block, width, height, x_crop, y_crop)
        terminal.draw_block(block, x, y, self.default_format or default_format)

    def _update(self, default_format, terminal):
        self._draw(
            *self._previous_geometry,
            default_format=self.default_format or default_format,
            terminal=terminal)

    @abstractmethod
    def _get_block(self, width, height):
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

    def _get_cropped_block(self, width, height):
        '''Sanitises the output from the element's _get_lines method to make
        sure that it is the correct shape according to width and height.
        '''
        full_width = clamp(width, min_=self.min_width, max_=self.max_width)
        full_height = clamp(height, min_=self.min_height, max_=self.max_height)
        lines = self._get_block(full_width, full_height)
        lines = self._do_crop(
            lines, full_width, full_height, self._halign, self._valign)
        return lines


class Fill(ABCDisplayElement):
    def __init__(self, char='.', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char = char

    def _get_block(self, width, height):
        return [self.char * width] * height


class Label(ABCDisplayElement):
    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def _get_block(self, width, height):
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

    def _get_block(self, width, height):
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

    def _get_block(self, width, height):
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
