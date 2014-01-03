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
    '''
    :parameter element: The element that will be drawn when the root is
        drawn. (Optional, can be reassigned at any time.)
    :parameter terminal: An instance of a :class:`Terminal` object to use
        for communication with your TTY. (Optional, we will grab a default
        and can be reassigned so long as we're not currently running.)
    :parameter loop: The asyncio event loop to use for the main :meth:`run`
        method. (Optional, we will grab a default if none is provided, and
        the loop can be reassigned so long as we're not currently running.)

    A :class:`Root` object will normally form the nucleus of your application.
    It performs three key roles:

    * Managing running the default :class:`Terminal` and the :mod:`asyncio`
      event loop
    * Providing easy access to add formats and styles to your applications
      content via :attr:`format` and :attr:`style`
    * Acting as the base of a tree of UI elements (instances of
      :class:`ABCUIElement`)

    A simple example of all three of these roles can be found in
    ``examples/quick_brown_fox.py``:

    .. literalinclude:: ../../examples/quick_brown_fox.py
        :lines: 16-

    '''
    format = FormatPlaceholderFactory()
    style = StylePlaceholderFactory()

    def __init__(self, element=None, terminal=None, loop=None):
        super().__init__()
        self._element = None
        if element:
            self.element = element
        # FIXME: should terminal and loop be passed in for run() only?
        self.terminal = terminal or get_terminal()
        self.loop = loop or asyncio.get_event_loop()
        self.keyboard = Keyboard()
        # FIXME: we should probably inherit from ABCContainerElement so that we
        # get stuff like child.updated tracking by default:
        self._updated = True

    @property
    def element(self):
        '''A reference to a single :class:`ABCUIElement` instance, most likely
        a container element, that forms the foundation of your UI. This element
        will be drawn or updated whenever a request comes to this :class:`Root`
        instance to do the same.
        '''
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
        '''``True`` if this element, or any of its children, have been
        updated, otherwise ``False``.
        '''
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
        '''The main entry point of a :mod:`jcn`-based application. :meth:`run`
        sets up the terminal and then runs then event loop, continually
        responding to user input and drawing UI element to the screen when
        required.

        Specifically, :mod:`jcn` applications run the terminal full-screen and
        with the cursor hidden, and set :attr:`sys.stdin` to unbuffered and
        non-blocking so that we can respond immediately to any keystrokes from
        the user. We also correctly handle being suspended (:kbd:`Control-z`,
        SIGTSTP) and resumed, and the terminal window being resized.

        We run :mod:`asyncio` event loop inside context managers that will
        handle exceptions gracefully and return the terminal to the previous
        state before exiting. Aren't we nice ;-)
        '''
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
        '''Draw the tree of UI elements once directly to the terminal. The root
        element of the UI is referenced by this instance's :attr:`element`
        attribute. Layout is automatically calculated by the UI elements in the
        tree in reponse ultimately to the :attr:`width` and :attr:`height`
        attributes of this instances :class:`Terminal`: instance. There is no
        async behaviour triggered from this method - see :meth:`run` if you
        want to :mod:`jcn` to take care redrawing when required.
        '''
        super().draw(
            self.terminal.width, self.terminal.height, terminal=self.terminal,
            styles=self.style)

    def update(self):
        '''Draws directly to the terminal any UI elements in the tree that are
        marked as having been updated. UI elements may have marked themselves
        as updated if, for example, notable attributes have been altered, or
        the :attr:`updated` element may be set to ``True`` explicitly by your
        program. The drawing and layout logic are exactly the same as for
        :meth:`draw`.
        '''
        super().update(
            self.default_format, terminal=self.terminal, styles=self.style)

    def _get_all_blocks(self, *args, **kwargs):
        return self.element.get_all_blocks(*args, **kwargs)

    def _get_updated_blocks(self, *args, **kwargs):
        return self.element.get_updated_blocks(*args, **kwargs)
