from textwrap import wrap

from .base import ABCUIElement, ABCContainerElement, VAlign


class Fill(ABCUIElement):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    def __init__(self, fillchar='.'):
        super().__init__(fillchar=fillchar)

    def _draw(self, width, height):
        return []


class Text(ABCUIElement):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content

    def _draw(self, width, height):
        return wrap(self.content, width)


class Stack(ABCContainerElement):
    max_width = None
    max_height = None

    def __init__(self, elements, valign=VAlign.bottom):
        super().__init__(elements)
        self.valign = valign

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

    def _draw(self, width, height):
        lines = []
        for element in self:
            lines.extend(element.draw(width, element.min_height or 1))
        return lines
