from unittest import TestCase

from junction.base import VAlign
from junction.util import weighted_round_robin


class TestUtil(TestCase):
    def test_weighted_round_robin(self):
        test_data = [('a', 3), ('b', 1), ('c', 2)]
        result = [
            val for val, _ in zip(weighted_round_robin(test_data), range(12))]
        expected = ['a', 'c', 'b', 'a', 'c', 'a'] * 2
        self.assertEqual(result, expected)
