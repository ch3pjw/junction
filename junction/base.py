from enum import Enum, unique
from abc import ABCMeta, abstractmethod, abstractproperty


@unique
class VAlign(Enum):
    top = 1
    middle = 2
    bottom = 3


@unique
class HAlign(Enum):
    left = 1
    center = 2
    right = 3


class ABCUIElement(metaclass=ABCMeta):
    min_width = abstractproperty()
    max_width = abstractproperty()
    min_height = abstractproperty()
    max_height = abstractproperty()

    @abstractmethod
    def _draw(self, width, height):
        pass

    def __init__(self, halign=HAlign.left, valign=VAlign.top, fillchar=' '):
        self._halign = None
        self._valign = None
        self.halign = halign
        self.valign = valign
        self.fillchar = fillchar

    @property
    def halign(self):
        return self._halign

    @halign.setter
    def halign(self, value):
        '''We define a setter because it's better to diagnose this kind of
        programmatic error here than have to work out why alignment is odd when
        we sliently fail!
        '''
        if value not in HAlign:
            raise ValueError(
                "Can't set non-existant HAlign {!r} on element {!r}".format(
                    value, self))
        self._halign = value

    @property
    def valign(self):
        return self._valign

    @valign.setter
    def valign(self, value):
        '''We define a setter because it's better to diagnose this kind of
        programmatic error here than have to work out why alignment is odd when
        we sliently fail!
        '''
        if value not in VAlign:
            raise ValueError(
                "Can't set non-existant VAlign {!r} on element {!r}".format(
                    value, self))
        self._valign = value

    def _horizontally_bound_output(self, draw_output, width):
        for i, line in enumerate(draw_output):
            if len(line) > width:
                draw_output[i] = line[:width]
            else:
                if self._halign is HAlign.left:
                    draw_output[i] = line.ljust(width, self.fillchar)
                elif self._halign is HAlign.center:
                    draw_output[i] = line.center(width, self.fillchar)
                elif self._halign is HAlign.right:
                    draw_output[i] = line.rjust(width, self.fillchar)
        return draw_output

    def _vertically_bound_output(self, draw_output, width, height):
        if len(draw_output) > height:
            if self._valign is VAlign.top:
                slice_ = slice(None, height)
            elif self._valign is VAlign.bottom:
                slice_ = slice(-height, None)
            elif self._valign is VAlign.middle:
                extra = len(draw_output) - height
                slice_ = slice(extra // 2, (extra + 1) // 2)
            result = draw_output[slice_]
        else:
            missing = height - len(draw_output)
            result = [self.fillchar * width] * missing
            if self._valign is VAlign.top:
                index = 0
            elif self._valign is VAlign.bottom:
                index = len(result)
            elif self._valign is VAlign.middle:
                index = len(result) // 2
            result[index:index] = draw_output
        return result

    def draw(self, width, height):
        draw_output = self._draw(width, height)
        draw_output = self._vertically_bound_output(draw_output, width, height)
        draw_output = self._horizontally_bound_output(draw_output, width)
        return draw_output


class ABCContainerElement(ABCUIElement):
    def __init__(self, elements, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = []
        for element in elements:
            self.add_element(element)

    def __iter__(self):
        return iter(self._content)

    def add_element(self, element):
        self._content.append(element)

    def remove_element(self, element):
        self._content.remove(element)
