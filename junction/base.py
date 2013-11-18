from abc import ABCMeta, abstractmethod


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

    def __repr__(self):
        if self.name:
            return '<{} element {!r}>'.format(
                self.__class__.__name__, self.name)
        else:
            return '<{} element at {}>'.format(
                self.__class__.__name__, hex(id(self)))

    @property
    def halign(self):
        return self._halign

    @halign.setter
    def halign(self, value):
        '''We define a setter because it's better to diagnose this kind of
        programmatic error here than have to work out why alignment is odd when
        we sliently fail!
        '''
        if value not in self._possible_haligns:
            if value in self._all_haligns:
                msg = 'non-permitted'
            else:
                msg = 'non-existant'
            raise ValueError(
                "Can't set {} horizontal alignment {!r} on element "
                "{!r}".format(msg, value, self))
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
        if value not in self._possible_valigns:
            if value in self._all_valigns:
                msg = 'non-permitted'
            else:
                msg = 'non-existant'
            raise ValueError(
                "Can't set {} vertical alignment {!r} on element "
                "{!r}".format(msg, value, self))
        self._valign = value

    @abstractmethod
    def draw(self, width, height, x=0, y=0, x_crop=None, y_crop=None):
        pass
