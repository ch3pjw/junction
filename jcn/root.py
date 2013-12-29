# Copyright (C) 2013 Paul Weaver <p.weaver@ruthorn.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

import asyncio
import signal
from contextlib import contextmanager

from .base import ABCUIElement
from .formatting import FormatPlaceholderFactory, StylePlaceholderFactory
from .terminal import get_terminal, Keyboard


class Root(ABCUIElement):
    format = FormatPlaceholderFactory()
    style = StylePlaceholderFactory()

    def __init__(self, element=None, styles=None, terminal=None, loop=None):
        '''Represents the root element of a tree of UI elements. We are
        associated with a Terminal object, so we're in the unique position of
        knowing our own width and height constraints, and are responsible for
        passing those down the tree when we are asked to draw ourselves.

        :parameter element: The element which will be drawn when the root is
            drawn. (Optional, can be reassigned at any time.)
        :parameter styles: A dictionary mapping names to particular Format or
            StringWithFormatting objects. (Optional.)
        :parameter terminal: An instnace of a junction.Terminal object to use
            for communication with your TTY. (Optional, we will grab a default
            and can be reassigned so long as we're not currently running.)
        :parameter loop: The asyncio event loop to use for the main ``run()``
            method. (Optional, we will grab a default if none is provided, and
            the loop can be reassigned so long as we're not currently running.)
        '''
        super().__init__()
        self._element = None
        if element:
            self.element = element
        self.styles = styles
        self.terminal = terminal or get_terminal()
        self.loop = loop or asyncio.get_event_loop()
        self.keyboard = Keyboard()
        # FIXME: we should probably inherit from ABCContainerElement so that we
        # get stuff like child.updated tracking by default:
        self._updated = True

    @property
    def element(self):
        return self._element

    @element.setter
    def element(self, new_element):
        if self._element:
            self._element.root = None
        self._element = new_element
        if new_element:
            new_element.root = self

    @property
    def updated(self):
        return self.element.updated or self._updated

    @updated.setter
    def updated(self, value):
        self._updated = True

    @contextmanager
    def _handle_screen_resize(self):
        signal.signal(signal.SIGWINCH, self._on_screen_resize)
        try:
            yield
        finally:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

    def _on_screen_resize(self, sig_num, stack_frame):
        self.draw()

    def run(self):
        with self.terminal.fullscreen(), self.terminal.hidden_cursor(), (
                self.terminal.unbuffered_input()), (
                self.terminal.nonblocking_input()), (
                self._handle_screen_resize()):
            def read_stdin():
                data = self.terminal.infile.read()
                self.element.handle_input(self.keyboard[data])
            if self.terminal.infile.isatty():
                self.loop.add_reader(self.terminal.infile, read_stdin)
            self.draw()
            self.loop.run_forever()

    def draw(self):
        super().draw(
            self.terminal.width, self.terminal.height, terminal=self.terminal,
            styles=self.styles)

    def update(self):
        super().update(
            self.default_format, terminal=self.terminal, styles=self.styles)

    def _get_all_blocks(self, *args, **kwargs):
        return self.element.get_all_blocks(*args, **kwargs)

    def _get_updated_blocks(self, *args, **kwargs):
        return self.element.get_updated_blocks(*args, **kwargs)
