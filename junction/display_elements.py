from abc import abstractmethod

from .base import ABCUIElement
from .util import clamp, crop_or_expand
from .terminal import get_terminal
from .formatting import StringWithFormatting, wrap


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
        term.draw_block(block, x, y, self.default_format)

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
            lines[-1] += self.terminal.normal
        return lines


class LineBuffer:
    # Yes, the irony of re-implementing a bunch of stuff we've gone out of way
    # to turn off in the terminal is not lost on me ;-)
    def __init__(self):
        self.content = ''
        self.cursor_position = 0

    def __bool__(self):
        return bool(self.content)

    def __len__(self):
        return len(self.content)

    def __str__(self):
        return self.content

    def clear(self):
        self.content = ''

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

    def _insert_char(self, char):
        pos = self.cursor_position
        if pos == len(self.content):
            self.content += char
        else:
            self.content = self.content[:pos] + char + self.content[pos:]
        self.cursor_position += 1

    def _backspace_char(self):
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


class Input(Text):
    # I'm not sure I'm liking the contstraints that the interrelationship of
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
        # FIXME: this is a temporary hack to try proof of concept
        self.root.draw()

    def _get_block(self, width, height):
        if self.line_buffer:
            return [str(self.line_buffer)]
        else:
            return [self.placeholder_text]


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
