from abc import abstractmethod

from .base import ABCUIElement
from .terminal import get_terminal


class ABCContainerElement(ABCUIElement):
    def __init__(self, elements=None, *args, **kwargs):
        self._content = []
        self._active_element = None
        self._terminal = None
        super().__init__(*args, **kwargs)
        elements = elements or []
        for element in elements:
            self.add_element(element)

    def __iter__(self):
        return iter(self._content)

    @property
    def terminal(self):
        return self._terminal

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

    def draw(self, width, height, x=0, y=0, x_crop=None, y_crop=None):
        for element, width, height, x, y in (
                self._get_elements_sizes_and_positions(width, height, x, y)):
            element.draw(
                width, height, x, y, x_crop=self._halign, y_crop=self._valign)


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


class Stack(ABCContainerElement):
    max_width = None
    max_height = None
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
