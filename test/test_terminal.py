from unittest import TestCase
import blessings
from io import StringIO

from junction import Terminal
from junction.terminal import get_terminal


class TestTerminal(TestCase):
    def test_draw_block(self):
        self.maxDiff = 0  # protect from difficult terminal output on failure
        blessings_term = blessings.Terminal(force_styling=True)
        test_term = Terminal()
        test_term.stream = StringIO()
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
