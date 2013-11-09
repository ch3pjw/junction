import blessings


class Root:
    def __init__(self, element, terminal=None):
        '''Represents the root element of a tree of UI elements. We are
        associated with a blessings.Terminal object, so we're in the unique
        position of knowing our own width and height constraints, and are
        responsible for passing those down the tree when we are asked to draw
        ourselves.

        :parameter element: The element which will be drawn when the root is
            drawn.
        '''
        self.element = element
        self.terminal = terminal or blessings.Terminal()

    @property
    def width(self):
        return self.terminal.width

    @property
    def height(self):
        return self.terminal.height

    def draw(self, width, height):
        return self.element.draw(width, height)

    def __str__(self):
        return '\n'.join(self.draw(self.width, self.height))
