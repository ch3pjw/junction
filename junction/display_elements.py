from abc import abstractmethod
from textwrap import wrap

from .base import ABCUIElement
from .util import clamp, crop_or_expand
from .terminal import get_terminal


class ABCDisplayElement(ABCUIElement):
    _scheme = {
        'left': 'beginning',
        'center': 'middle',
        'right': 'end',
        'top': 'beginning',
        'middle': 'middle',
        'bottom': 'end'}

    def _draw(self, width, height, x, y, x_crop, y_crop):
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
        term = self.terminal or get_terminal()
        block = self._get_cropped_block(width, height)
        # Perform an additional crop with *different alignment* to resize the
        # UI element's rendered area text to the required area:
        block = self._do_crop(block, width, height, x_crop, y_crop)
        term.draw_block(block, x, y)

    def _update(self):
        self._draw(*self._previous_geometry)

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


class Text(ABCDisplayElement):
    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def _get_block(self, width, height):
        return wrap(self.content, width)
