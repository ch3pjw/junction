from unittest import TestCase

from junction.elements import Fill


class TestElements(TestCase):
    def test_fill(self):
        fill = Fill()
        self.assertEqual(fill.draw(10, 0), [])
        self.assertEqual(fill.draw(10, 1), ['..........'])
        self.assertEqual(fill.draw(2, 2), ['..', '..'])
        self.assertEqual(fill.draw(0, 4), ['', '', '', ''])
        fill = Fill('o')
        self.assertEqual(fill.draw(1, 1), ['o'])
