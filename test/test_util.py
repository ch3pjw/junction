from unittest import TestCase

from junction.util import weighted_round_robin, fixed_length_list, VAlign


class TestUtil(TestCase):
    def test_weighted_round_robin(self):
        test_data = [('a', 3), ('b', 1), ('c', 2)]
        result = [
            val for val, _ in zip(weighted_round_robin(test_data), range(12))]
        expected = ['a', 'c', 'b', 'a', 'c', 'a'] * 2
        self.assertEqual(result, expected)

    def test_fixed_length_list(self):
        self.assertEqual(fixed_length_list([1, 2, 3], 3), [1, 2, 3])
        self.assertEqual(fixed_length_list([1, 2, 3, 4], 3), [1, 2, 3])
        self.assertEqual(fixed_length_list([1, 2, 3], 4), [1, 2, 3, ''])
        self.assertEqual(
            fixed_length_list([], 3, default='moo'),
            ['moo', 'moo', 'moo'])
        self.assertEqual(
            fixed_length_list([1], 5, valign=VAlign.bottom),
            ['', '', '', '', 1])
        self.assertEqual(
            fixed_length_list([2], 5, valign=VAlign.middle),
            ['', '', 2, '', ''])
        self.assertEqual(
            fixed_length_list([3], 4, valign=VAlign.middle),
            ['', 3, '', ''])
