from abc import ABCMeta, abstractmethod
from collections import namedtuple


Geometry = namedtuple(
    'Geometry', ['width', 'height', 'x', 'y', 'x_crop', 'y_crop'])


class ABCUIElement(metaclass=ABCMeta):
    min_width = None
    max_width = None
    min_height = None
    max_height = None

    _all_valigns = 'top', 'middle', 'bottom'
    _possible_valigns = _all_valigns
    _all_haligns = 'left', 'center', 'right'
    _possible_haligns = _all_haligns

    def __init__(self, halign='left', valign='top', fillchar=' ', name=''):
        self._halign = None
        self._valign = None
        self.halign = halign
        self.valign = valign
        self.fillchar = fillchar
        self.name = name
        self.terminal = None
        self.updated = True
        self._previous_geometry = None

    def __repr__(self):
        if self.name:
            return '<{} element {!r}>'.format(
                self.__class__.__name__, self.name)
        else:
            return '<{} element at {}>'.format(
                self.__class__.__name__, hex(id(self)))

    def _set_align(self, orientation, value):
        '''We define a setter because it's better to diagnose this kind of
        programmatic error here than have to work out why alignment is odd when
        we sliently fail!
        '''
        orientation_letter = orientation[0]
        possible_alignments = getattr(
            self, '_possible_{}aligns'.format(orientation_letter))
        all_alignments = getattr(
            self, '_all_{}aligns'.format(orientation_letter))
        if value not in possible_alignments:
            if value in all_alignments:
                msg = 'non-permitted'
            else:
                msg = 'non-existant'
            raise ValueError(
                "Can't set {} {} alignment {!r} on element {!r}".format(
                    msg, orientation, value, self))
        setattr(self, '_{}align'.format(orientation_letter), value)

    @property
    def halign(self):
        return self._halign

    @halign.setter
    def halign(self, value):
        self._set_align('horizontal', value)

    @property
    def valign(self):
        return self._valign

    @valign.setter
    def valign(self, value):
        self._set_align('vertical', value)

    def draw(self, width, height, x=0, y=0, x_crop='left', y_crop='top'):
        self._draw(width, height, x, y, x_crop, y_crop)
        self._previous_geometry = Geometry(width, height, x, y, x_crop, y_crop)
        self.updated = False

    @abstractmethod
    def _draw(self, width, height, x, y, x_crop, y_crop):
        pass

    def update(self):
        if self._previous_geometry is None:
            raise ValueError("draw() must be called on {!r} before it can be "
                             "updated".format(self))
        self._update()
        self.updated = False

    @abstractmethod
    def _update(self):
        pass
