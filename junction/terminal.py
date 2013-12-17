import blessings
import termios
import tty
import signal
import os
import sys
import fcntl
from functools import wraps
from contextlib import contextmanager

from .formatting import Format, StringWithFormatting


def _override_sugar(func):
    '''Use this decorator to override an attribute that is specified in
    blessings' sugar dict with your own function that adds some additional
    functionality.
    '''
    attr_name = func.__name__
    @property
    @wraps(func)
    def func_that_uses_terminal_sugar(self):
        func(self)
        return self.__getattr__(attr_name)
    return func_that_uses_terminal_sugar


class Terminal(blessings.Terminal):
    def __init__(self, *args, infile=None, handle_signals=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.infile = infile or sys.stdin
        if handle_signals:
            signal.signal(signal.SIGTSTP, self._handle_sigtstp)
        if self.is_a_tty:
            self._orig_tty_attrs = termios.tcgetattr(self.stream)
        else:
            self._orig_tty_attrs = None
        # We track these to make SIGTSTP restore the terminal correctly:
        self._is_fullscreen = False
        self._has_hidden_cursor = False
        self._normal = super()._resolve_formatter('normal')
        self._resolved_sugar_cache = {}

    def __getattr__(self, attr):
        '''We override ___getattr__ so that we don't do blessings' annoying
        caching by attribute-setting side-effect! This means we can override
        sugar without fear! See the _override_sugar decorator.
        '''
        try:
            return self._resolved_sugar_cache[attr]
        except KeyError:
            if self._does_styling:
                resolution = self._resolve_formatter(attr)
            else:
                resolution = blessings.NullCallableString()
            self._resolved_sugar_cache[attr] = resolution
            return resolution

    @_override_sugar
    def enter_fullscreen(self):
        self._is_fullscreen = True

    @_override_sugar
    def exit_fullscreen(self):
        self._is_fullscreen = False

    @_override_sugar
    def hide_cursor(self):
        self._has_hidden_cursor = True

    @_override_sugar
    def normal_cursor(self):
        self._has_hidden_cursor = False

    @property
    def color(self):
        return Format(super().color, name='color')

    @property
    def on_color(self):
        return Format(super().on_color, name='on_color')

    def _handle_sigtstp(self, sig_num, stack_frame):
        # Store current state:
        if self.is_a_tty:
            cur_tty_attrs = termios.tcgetattr(self.stream)
            termios.tcsetattr(
                self.stream, termios.TCSADRAIN, self._orig_tty_attrs)
        is_fullscreen = self._is_fullscreen
        has_hidden_cursor = self._has_hidden_cursor
        # Restore normal terminal state:
        if is_fullscreen:
            self.stream.write(self.exit_fullscreen)
        if has_hidden_cursor:
            self.stream.write(self.normal_cursor)
        self.stream.flush()
        # Unfortunately, we have to remove our signal handler and
        # reinstantiate it after we're continued, because the only way we
        # can get python to sleep is if we send the signal to ourselves again
        # with no handler :-(
        current_handler = signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        def restore_on_sigcont(sig_num, stack_frame):
            signal.signal(signal.SIGTSTP, current_handler)
            signal.signal(signal.SIGCONT, signal.SIG_DFL)
            if self.is_a_tty:
                termios.tcsetattr(
                    self.stream, termios.TCSADRAIN, cur_tty_attrs)
            if is_fullscreen:
                self.stream.write(self.enter_fullscreen)
            if has_hidden_cursor:
                self.stream.write(self.hide_cursor)
        signal.signal(signal.SIGCONT, restore_on_sigcont)
        os.kill(os.getpid(), signal.SIGTSTP)

    @contextmanager
    def unbuffered_input(self):
        '''Sets cbreak on the current tty so that input from the user isn't
        parcelled up and delivered with each press of return, but delivered on
        each keystroke.
        '''
        if self.is_a_tty:
            orig_tty_attrs = termios.tcgetattr(self.stream)
            tty.setcbreak(self.stream)
            try:
                yield
            finally:
                termios.tcsetattr(
                    self.stream, termios.TCSADRAIN, orig_tty_attrs)
        else:
            yield

    @contextmanager
    def nonblocking_input(self):
        if hasattr(self.infile, 'fileno'):
            # Use fcntl to set stdin to non-blocking. WARNING - this is not
            # particularly portable!
            flags = fcntl.fcntl(self.infile, fcntl.F_GETFL)
            fcntl.fcntl(self.infile, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            try:
                yield
            finally:
                fcntl.fcntl(self.infile, fcntl.F_SETFL, flags)
        else:
            yield

    def draw_block(self, block, x, y, normal=None):
        if normal is not None:
            self.stream.write(normal)
        for y, line in enumerate(block, start=y):
            self.stream.write(self.move(y, x))
            if isinstance(line, StringWithFormatting):
                line = line.draw(normal or self._normal)
            self.stream.write(line)

    def _resolve_formatter(self, name):
        if name == 'normal':
            resolved = None
        else:
            resolved = super()._resolve_formatter(name)
        return Format(resolved, name=name)

_terminal = Terminal()


def get_terminal():
    return _terminal


class Keyboard:
    '''Utility class for turning key escape sequences into human-parsable key
    names.
    '''
    def __init__(self):
        self._sequence_to_name = {
            '\x1b': 'esc',
            ' ': 'space',

            '\x1b[A': 'up',
            '\x1b[B': 'down',
            '\x1b[C': 'right',
            '\x1b[D': 'left',
            '\x1b[E': 'keypad5',
            '\x1b[F': 'end',
            '\x1b[G': 'keypad5',
            '\x1b[H': 'home',

            '\x1b[1~': 'home',
            '\x1b[2~': 'insert',
            '\x1b[3~': 'delete',
            '\x1b[4~': 'end',
            '\x1b[5~': 'pageup',
            '\x1b[6~': 'pagedown',
            '\x1b[7~': 'home',
            '\x1b[8~': 'end',

            '\x1b[11~': 'f1', '\x1b[[A': 'f1', '\x1bOP': 'f1',
            '\x1b[12~': 'f2', '\x1b[[B': 'f2', '\x1bOQ': 'f2',
            '\x1b[13~': 'f3', '\x1b[[C': 'f3', '\x1bOR': 'f3',
            '\x1b[14~': 'f4', '\x1b[[D': 'f4', '\x1bOS': 'f4',
            '\x1b[15~': 'f5', '\x1b[[E': 'f5',

            '\t': 'tab',
            '\x1b[Z': 'shift tab',
            '\x7f': 'backspace'}
        self._sequence_to_name.update(self._create_high_f_keys())
        self._sequence_to_name.update(self._create_ctrl_keys())
        self._sequence_to_name.update(self._create_alt_keys())

    def _create_high_f_keys(self):
        # make normal key range:
        high_f_seq_nums = (n for n in range(17, 35) if n not in (22, 27, 30))
        f_num_seq_num = enumerate(high_f_seq_nums, start=6)
        high_f_keys = {'\x1d[%d~' % n: 'f%d' % f for f, n in f_num_seq_num}
        return high_f_keys

    def _create_ctrl_keys(self):
        ctrl_keys = {}
        for i in range(26):
            name = 'ctrl ' + chr(ord('a') + i - 1)
            sequence = chr(i)
            ctrl_keys[sequence] = name
        return ctrl_keys

    def _create_alt_keys(self):
        alt_keys = {}
        for i in range(33, 127):
            name = 'alt ' + chr(i)
            sequence = '\x1b{}'.format(chr(i))
            alt_keys[sequence] = name
        return alt_keys

    def __getitem__(self, sequence):
        if sequence in self._sequence_to_name:
            return self._sequence_to_name[sequence]
        else:
            return sequence
