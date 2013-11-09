from unittest import TestCase
from mock import Mock

from junction.root import Root
from junction.elements import Fill


class TestRoot(TestCase):
    def test_root(self):
        fill = Fill()
        mock_terminal = Mock()
        mock_terminal.width = 5
        mock_terminal.height = 3
        root = Root(fill, mock_terminal)
        self.assertEqual(root.draw(2, 2), ['..', '..'])
        self.assertEqual(str(root), '.....\n.....\n.....')
