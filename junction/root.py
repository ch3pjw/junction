import asyncio
import signal
from contextlib import contextmanager

from .formatting import FormatFactory
from .terminal import get_terminal, Keyboard


class Root:
    format = FormatFactory()

    def __init__(self, element, *args, terminal=None, loop=None, **kwargs):
        '''Represents the root element of a tree of UI elements. We are
        associated with a Terminal object, so we're in the unique position of
        knowing our own width and height constraints, and are responsible for
        passing those down the tree when we are asked to draw ourselves.

        :parameter element: The element which will be drawn when the root is
            drawn.
        '''
        self.element = element
        element.root = self
        self.terminal = terminal or get_terminal()
        self.loop = loop or asyncio.get_event_loop()
        self.element.terminal = self.terminal
        self.keyboard = Keyboard()

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
        self.element.draw(self.terminal.width, self.terminal.height)
        self.terminal.stream.flush()

    def update(self):
        self.element.update()
        self.terminal.stream.flush()
