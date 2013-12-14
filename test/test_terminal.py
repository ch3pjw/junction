from unittest import TestCase
from mock import patch

import blessings
import signal
import os
from io import StringIO

from junction import Terminal
from junction.terminal import get_terminal


class TestTerminal(TestCase):
    def test_overridden_sugar(self):
        junction_terminal = Terminal(force_styling=True)
        blessings_terminal = blessings.Terminal(force_styling=True)
        for attr_name in (
                'enter_fullscreen', 'exit_fullscreen', 'hide_cursor',
                'normal_cursor'):
            # Check that we're actually behaving like a tty:
            self.assertTrue(bool(getattr(blessings_terminal, attr_name)))
            # Check normal retrieval
            self.assertEqual(
                getattr(junction_terminal, attr_name),
                getattr(blessings_terminal, attr_name))
            # We check retrieval a second time because we cache:
            self.assertEqual(
                getattr(junction_terminal, attr_name),
                getattr(blessings_terminal, attr_name))

    @patch('junction.terminal.termios', autospec=True)
    @patch('junction.terminal.signal.signal', autospec=True)
    @patch('junction.terminal.os.kill', autospec=True)
    def test_handle_sigtstp(self, mock_kill, mock_signal, mock_termios):
        # This is quite a poor unit test, in the sense that it basically
        # checks that the code I've written is the code I've written! Any
        # suggestions on how to test this in a less invasive way are welcome!
        mock_termios.tcgetattr.return_value = 'Wobble'
        mock_signal.return_value = 'current_handler'
        fake_tty = StringIO()
        term = Terminal(stream=fake_tty, force_styling=True)
        term._is_fullscreen = True
        term._has_hidden_cursor = True
        term.is_a_tty = True
        term.handle_sigtstp(None, None)
        mock_termios.tcgetattr.assert_called_once_with(fake_tty)
        self.assertTrue(bool(fake_tty.getvalue()))
        self.assertIn(term.exit_fullscreen, fake_tty.getvalue())
        self.assertIn(term.normal_cursor, fake_tty.getvalue())
        mock_signal.assert_any_call(signal.SIGTSTP, signal.SIG_DFL)
        signal_obj, cont_handler = mock_signal.call_args[0]
        self.assertEqual(signal_obj, signal.SIGCONT)
        mock_kill.assert_called_once_with(os.getpid(), signal.SIGTSTP)

        fake_tty.truncate(0)
        cont_handler(None, None)
        mock_signal.assert_any_call(signal.SIGTSTP, 'current_handler')
        mock_signal.assert_any_call(signal.SIGCONT, signal.SIG_DFL)
        self.assertIn(term.enter_fullscreen, fake_tty.getvalue())
        self.assertIn(term.hide_cursor, fake_tty.getvalue())
        mock_termios.tcsetattr.assert_called_with(
            fake_tty, mock_termios.TCSADRAIN, 'Wobble')

    def test_getattr(self):
        term = Terminal()
        term._does_styling = False
        self.assertIsInstance(term.blue, blessings.NullCallableString)

    def test_draw_block(self):
        self.maxDiff = 0  # protect from difficult terminal output on failure
        blessings_term = blessings.Terminal(force_styling=True)
        test_term = Terminal(stream=StringIO(), force_styling=True)
        test_term.draw_block(['hello', 'world'], x=3, y=4)
        self.assertEqual(
            test_term.stream.getvalue(),
            blessings_term.move(4, 3) + 'hello' +
            blessings_term.move(5, 3) + 'world')

    def test_get_terminal(self):
        terminal = get_terminal()
        self.assertIsInstance(terminal, Terminal)
        # Same terminal instance every time:
        self.assertIs(get_terminal(), terminal)
