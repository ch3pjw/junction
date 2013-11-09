from textwrap import wrap

from .base import ABCUIElement, ABCContainerElement
from .util import fixed_length_list, VAlign, HAlign


class Fill(ABCUIElement):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    def __init__(self, fillchar='.'):
        self.fillchar = fillchar

    def draw(self, width, height):
        return [self.fillchar * width] * height


class Text(Fill):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    def __init__(self, content, halign=HAlign.left, valign=VAlign.top,
                 fillchar=' '):
        super().__init__(fillchar)
        self.content = content
        self.halign = halign
        self.valign = valign

    def draw(self, width, height):
        lines = fixed_length_list(
            wrap(self.content, width), height, valign=self.valign)
        for i, line in enumerate(lines):
            if self.halign is HAlign.left:
                lines[i] = line.ljust(width, self.fillchar)
            elif self.halign is HAlign.center:
                lines[i] = line.center(width, self.fillchar)
            elif self.halign is HAlign.right:
                lines[i] = line.rjust(width, self.fillchar)
        return lines


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

    def draw(self, width, height):
        lines = []
        for element in self:
            lines.extend(element.draw(width, element.min_height or 1))
        return fixed_length_list(
            lines, height, default=' ' * width, valign=self.valign)
