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

import blessings
import termios
import tty
import signal
import os
import sys
import fcntl
from functools import wraps
from contextlib import contextmanager


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
    '''Junction is loosely based on the :mod:`blessings` module, which provides
    easy, Pythonic access to escape squences for terminal colouring, styling
    and positioning. Central to :mod:`blessings` is its
    :class:`blessings.Terminal` class, which is the hook for :mod:`blessings`'
    users to request escape sequences. Junction's :class:`Terminal` class
    extends :class:`blessings.Terminal` to add some features requisite for
    handling some more 'application level' situations.

    * Firstly, :class:`jcn.Terminal` overrides some of :mod:`blessings` normal
      methods to track some state of the terminal it is representing. This is
      important for handling suspension of the application via SIGTSTP
      correctly.  (In that case we need to restore the terminal's original
      behaviours when we are suspended and restore the application's desired
      behaviours when resumed.)

    * Secondly, we provide some methods to change the behaviour of
      :attr:`sys.stdin`, which :mod:`blessings` never needed to address, so
      that Junction applications can gain access to and handle user keystrokes
      responsively.

    * Finally, because Junction is all about drawing blocks of UI to the
      screen, rather than whole lines, we provide a simple inferface for doing
      that.

    You could create :class:`Terminal` instance manually, and use it
    independently or pass it to your applications :class:`Root` instance if you
    want to override some default behaviours, but in the *vast majority* of
    cases you just need to know that this is where :mod:`jcn`'s link to
    :mod:`blessings` lies, and the things this class takes care of so that you
    don't have to worry about them. To gain access to terminal formatting in
    your application, you instead use :attr:`Root.format`.
    '''
    def __init__(self, *args, infile=None, handle_signals=True, **kwargs):
        '''
        :parameter infile:
        :paremeter handle_signals:
        '''
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
        '''Context manager for setting the terminal to use unbuffered input.

        Normally, your terminal will collect together a user's input
        keystrokes and deliver them to you in one neat parcel when they hit
        the return/enter key. In a real-time interactive application we instead
        want to receive each keystroke as it happens.

        This context manager achieves that by setting 'cbreak' mode on the
        the output tty stream. cbreak is a mode inbetween 'cooked mode', where
        all the user's input is preprocessed, and 'raw mode' where none of it
        is. Basically, in cbreak mode input like :kbd:`Control-c` will still
        interrupt (i.e. 'break') the process, hence the name. Wikipedia is your
        friend on this one!

        :meth:`Root.run` uses this context manager for you to make your
        application work in the correct way.
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
        '''Context manager to set the :class:`Terminal`'s input file to read in
        a non-blocking way.

        Normally, reading from :attr:`sys.stdin` blocks, which is bad if we
        want an interactive application that can also update information on the
        screen without any input from the user! Therefore, we need to make
        :meth:`Terminal.infile.read` a non-blocking operation, which just
        returns nothing if we have no input.

        :meth:`Root.run` uses this context manager for you to make your
        application work in the correct way.
        '''
        # FIXME: do we handle restoring this during SIGTSTP?
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

    def draw_lines(self, lines, x=0, y=0):
        '''Write a collection of lines to the terminal stream at the given
        location. The lines are written as one 'block' (i.e. each new line
        starts one line down from the previous, but each starts *at the given x
        coordinate*).

        :parameter lines: An iterable of strings that should be written to the
            terminal. They need not all be the same length, but should ideally
            not extend beyond the right hand side of the terminal screen,
            otherwise strange linebreaking/overwriting may occur.
        :parameter x: the column of the terminal display at which the block of
            lines begins.
        :parameter y: the row of the terminal display at which the block of
            lines begins (from top).
        '''
        for y, line in enumerate(lines, start=y):
            self.stream.write(self.move(y, x))
            self.stream.write(line)

_terminal = Terminal()


def get_terminal():
    '''Explain why we have a :func:`get_terminal` - i.e. it's like the
    :func:`asyncio.get_event_loop` in that it will always return us a singleton
    instance. (If indeed that's something we actually care about any more?)
    '''
    return _terminal


class Keyboard:
    '''Utility class for turning key escape sequences into human-parsable key
    names.
    '''
    def __init__(self):
        self._sequence_to_name = {
            '\x1b': 'esc',
            ' ': 'space',
            '\n': 'return',

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
            if i != 10:
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
