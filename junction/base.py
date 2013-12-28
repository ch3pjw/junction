from abc import ABCMeta, abstractmethod
from collections import namedtuple

from .terminal import get_terminal
from .formatting import StringWithFormatting, EscapeSequenceStack


Geometry = namedtuple(
    'Geometry', ['width', 'height', 'x', 'y', 'x_crop', 'y_crop'])


class Block:
    __slots__ = 'x', 'y', 'lines', 'default_format'

    def __init__(self, x, y, lines, default_format):
        self.x = x
        self.y = y
        self.lines = lines
        self.default_format = default_format

    def __repr__(self):
        args = [self.x, self.y, self.lines]
        if self.default_format:
            args.append(self.default_format)
        return '{}({})'.format(
            self.__class__.__name__, ', '.join(str(arg) for arg in args))

    def __eq__(self, other):
        try:
            return all(
                getattr(self, attr_name) == getattr(other, attr_name) for
                attr_name in self.__slots__)
        except AttributeError:
            return False

    def __iter__(self):
        return iter(self.lines)


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
        self.updated = True
        self._previous_geometry = None
        self._default_format = None
        self.root = None

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
        self.updated = True

    @property
    def valign(self):
        return self._valign

    @valign.setter
    def valign(self, value):
        self._set_align('vertical', value)
        self.updated = True

    @property
    def default_format(self):
        return self._default_format

    @default_format.setter
    def default_format(self, value):
        self._default_format = value
        self.updated = True

    def draw(self, width, height, x=0, y=0, x_crop='left', y_crop='top',
             terminal=None, styles=None):
        blocks = self.get_all_blocks(
            width, height, x, y, x_crop, y_crop,
            default_format=self.default_format)
        self._do_draw(blocks, terminal, styles)

    def update(self, default_format=None, terminal=None, styles=None):
        blocks = self.get_updated_blocks(default_format)
        self._do_draw(blocks, terminal, styles)

    def _do_draw(self, blocks, terminal, styles):
        terminal = terminal or get_terminal()
        styles = styles or {}
        esc_seq_stack = EscapeSequenceStack(terminal.normal)
        for block in blocks:
            # FIXME: default formats are not additive - e.g. if the parent sets
            # underline as default and the child sets blue, we don't actually
            # apply both styles... :-(
            if block.default_format:
                def_esq_seq = block.default_format.populate(terminal, styles)
                terminal.stream.write(def_esq_seq)
                esc_seq_stack.push(def_esq_seq)
            lines = self._populate_lines(
                block.lines, terminal, styles, esc_seq_stack)
            terminal.draw_lines(lines, block.x, block.y)
            if block.default_format:
                terminal.stream.write(esc_seq_stack.pop())
        terminal.stream.flush()

    def _populate_lines(self, lines, terminal, styles, esc_seq_stack):
        '''Takes some lines to draw to the terminal, which may contain
        formatting placeholder objects, and inserts the appropriate concrete
        escapes sequences by using data from the terminal object and styles
        dictionary.
        '''
        for i, line in enumerate(lines):
            if isinstance(line, StringWithFormatting):
                line = line.populate(terminal, styles, esc_seq_stack)
            yield line

    def get_all_blocks(
            self, width, height, x=0, y=0, x_crop='left', y_crop='top',
            default_format=None):
        blocks = self._get_all_blocks(
            width, height, x, y, x_crop, y_crop, default_format)
        self._previous_geometry = Geometry(width, height, x, y, x_crop, y_crop)
        self.updated = False
        return blocks

    @abstractmethod
    def _get_all_blocks(
            self, width, height, x, y, x_crop, y_crop, default_format):
        pass

    def get_updated_blocks(self, default_format=None):
        if self._previous_geometry is None:
            raise ValueError("draw() must be called on {!r} before it can be "
                             "updated".format(self))
        blocks = []
        if self.updated:
            blocks.extend(self._get_updated_blocks(default_format))
            self.updated = False
        return blocks

    @abstractmethod
    def _get_updated_blocks(self, default_format):
        pass

    #@abstractmethod
    def handle_input(self, data):
        print('woo', data)
