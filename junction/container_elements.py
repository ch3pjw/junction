from abc import abstractmethod

from .base import ABCUIElement
from .terminal import get_terminal


class ABCContainerElement(ABCUIElement):
    def __init__(self, *elements, **kwargs):
        self._content = []
        self._active_element = None
        super().__init__(**kwargs)
        for element in elements:
            self.add_element(element)

    def __iter__(self):
        return iter(self._content)

    @property
    def terminal(self):
        return self._terminal or get_terminal()

    @terminal.setter
    def terminal(self, terminal):
        self._terminal = terminal
        for element in self:
            element.terminal = terminal

    @abstractmethod
    def _get_elements_sizes_and_positions(self, width, height, x, y):
        '''Returns an interable containing each element with its corresponding
        dimenions and position.
        '''

    def add_element(self, element):
        self._content.append(element)
        self._active_element = element
        element.terminal = self.terminal

    def remove_element(self, element):
        self._content.remove(element)

    def _draw(self, width, height, x=0, y=0, x_crop=None, y_crop=None):
        x_crop = x_crop or self._halign
        y_crop = y_crop or self._valign
        for element, width, height, x, y in (
                self._get_elements_sizes_and_positions(width, height, x, y)):
            element.draw(
                width, height, x, y, x_crop=x_crop, y_crop=y_crop)

    def _update(self):
        for element in self:
            print('here', element)
            if element.updated:
                print('there', element.updated)
                element.update()


class Root:
    def __init__(self, element, terminal=None, *args, **kwargs):
        '''Represents the root element of a tree of UI elements. We are
        associated with a Terminal object, so we're in the unique position of
        knowing our own width and height constraints, and are responsible for
        passing those down the tree when we are asked to draw ourselves.

        :parameter element: The element which will be drawn when the root is
            drawn.
        '''
        self.element = element
        self.terminal = terminal or get_terminal()
        self.element.terminal = self.terminal
        self.testing = False

    def run(self):
        with self.terminal.fullscreen():
            self.element.draw(self.terminal.width, self.terminal.height)
            if not self.testing:
                # FIXME: Blocking for now just to see output
                input()


class Box(ABCContainerElement):
    min_width = 2
    min_height = 2

    def __init__(self, content, chars=None, **kwargs):
        super().__init__(content, **kwargs)
        self._top_left = None
        self._top = None
        self._top_right = None
        self._right = None
        self._bottom_right = None
        self._bottom = None
        self._bottom_left = None
        self._left = None
        self.chars = chars

    @property
    def chars(self):
        return ''.join([
            self._top_left, self._top, self._top_right, self._right,
            self._bottom_right, self._bottom, self._bottom_left, self._left])

    @chars.setter
    def chars(self, chars):
        if not chars or len(chars) != 8:
            chars = '+-+|+-+|'
        self._top_left = chars[0]
        self._top = chars[1]
        self._top_right = chars[2]
        self._right = chars[3]
        self._bottom_right = chars[4]
        self._bottom = chars[5]
        self._bottom_left = chars[6]
        self._left = chars[7]
        self.updated = True

    @property
    def max_width(self):
        return self._active_element.max_width + 2

    @property
    def max_height(self):
        return self._active_element.max_height + 2

    def _get_elements_sizes_and_positions(self, width, height, x, y):
        yield self._active_element, width - 2, height - 2, x + 1, y + 1

    def _draw(self, width, height, x=0, y=0, *args, **kwargs):
        super()._draw(width, height, x, y, *args, **kwargs)
        top = [self._top_left + self._top * (width - 2) + self._top_right]
        left = [self._left] * (height - 2)
        bottom = [
            self._bottom_left + self._bottom * (width - 2) +
            self._bottom_right]
        right = [self._right] * (height - 2)
        self.terminal.draw_block(top, x, y, self.default_format)
        self.terminal.draw_block(left, x, y + 1, self.default_format)
        self.terminal.draw_block(
            bottom, x, y + height - 1, self.default_format)
        self.terminal.draw_block(
            right, x + width - 1, y + 1, self.default_format)


class Stack(ABCContainerElement):
    _possible_valigns = 'top', 'bottom'

    @property
    def min_width(self):
        try:
            return max(
                element.min_width for element in self if element.min_width)
        except ValueError:
            return

    @property
    def min_height(self):
        return sum(element.min_height or 1 for element in self)

    def _get_elements_sizes_and_positions(self, width, height, x, y):
        if self.valign == 'top':
            current_y = y
            for element in self:
                elem_height = min(height, element.min_height or 1)
                if elem_height:
                    yield element, width, elem_height, x, current_y
                    current_y += elem_height
                    height -= elem_height
                else:
                    break
        elif self.valign == 'bottom':
            current_y = y + height
            for element in reversed(self._content):
                elem_height = min(height, element.min_height or 1)
                if elem_height:
                    current_y -= elem_height
                    yield element, width, elem_height, x, current_y
                    height -= elem_height
                else:
                    break


class Zebra(Stack):
    def __init__(self, *args, odd_format=None, even_format=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.odd_format = odd_format
        self.even_format = even_format

    @property
    def _formats(self):
        return [
            self.even_format or self.default_format or self.terminal._normal,
            self.odd_format or self.default_format or self.terminal._normal]

    def _get_elements_sizes_and_positions(self, width, height, x, y):
        parent = super()._get_elements_sizes_and_positions(
            width, height, x, y)
        for i, (element, width, height, x, y) in enumerate(parent):
            element.default_format = self._formats[i % 2]
            yield element, width, height, x, y
