from .base import ABCUIElement


class Fill(ABCUIElement):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    def __init__(self, char='.'):
        self.char = char

    def draw(self, width, height):
        return [self.char * width] * height
