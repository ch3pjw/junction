from unittest import TestCase

from junction.util import clamp, weighted_round_robin, crop_or_expand


class TestUtil(TestCase):
    def test_clamp_values(self):
        self.assertEqual(clamp(1, 2, 3), 2)
        self.assertEqual(clamp(4, 3, 5), 4)
        self.assertEqual(clamp(10, 8, 9), 9)
        self.assertEqual(clamp(-1, 0, 1), 0)
        self.assertEqual(clamp(1, -1, 0), 0)

    def test_clamp_unbounded(self):
        self.assertEqual(clamp(42), 42)
        self.assertEqual(clamp(-42), -42)
        self.assertEqual(clamp(121, min_=13), 121)
        self.assertEqual(clamp(-121, min_=13), 13)
        self.assertEqual(clamp(121, max_=13), 13)
        self.assertEqual(clamp(-121, max_=13), -121)

    def test_weighted_round_robin(self):
        test_data = [('a', 3), ('b', 1), ('c', 2)]
        result = [
            val for val, _ in zip(weighted_round_robin(test_data), range(12))]
        expected = ['a', 'c', 'b', 'a', 'c', 'a'] * 2
        self.assertEqual(result, expected)

    def test_crop_or_expand_crop(self):
        self.assertEqual(crop_or_expand([1, 2, 3], 3), [1, 2, 3])
        self.assertEqual(crop_or_expand('abc', 3), 'abc')
        self.assertEqual(crop_or_expand([1, 2, 3, 4], 3), [1, 2, 3])
        self.assertEqual(crop_or_expand('abcd', 3), 'abc')
        self.assertEqual(crop_or_expand('abc', 2, scheme='beginning'), 'ab')
        self.assertEqual(
            crop_or_expand([1, 2, 3, 4], 3, scheme='end'),
            [2, 3, 4])
        self.assertEqual(crop_or_expand('abcd', 3, scheme='end'), 'bcd')
        self.assertEqual(
            crop_or_expand([1, 2, 3, 4, 5, 6], 2, scheme='middle'),
            [3, 4])
        self.assertEqual(crop_or_expand('abcdef', 2, scheme='middle'), 'cd')
        self.assertEqual(crop_or_expand('abcdef', 3, scheme='middle'), 'bcd')
        self.assertEqual(crop_or_expand('abcdefg', 3, scheme='middle'), 'cde')
        self.assertEqual(crop_or_expand('abcdefg', 2, scheme='middle'), 'cd')

    def test_crop_or_expand_expand(self):
        with self.assertRaises(TypeError):
            crop_or_expand([1, 2, 3], 4, default='bad')
        self.assertEqual(
            crop_or_expand([1, 2, 3], 4, default=['']),
            [1, 2, 3, ''])
        self.assertEqual(crop_or_expand('abc', 4), 'abc ')
        self.assertEqual(
            crop_or_expand([], 3, default=['moo']),
            ['moo', 'moo', 'moo'])
        self.assertEqual(crop_or_expand('', 2, default='baa'), 'baabaa')
        self.assertEqual(
            crop_or_expand([1], 5, scheme='end', default=['']),
            ['', '', '', '', 1])
        self.assertEqual(crop_or_expand('a', 6, scheme='end'), '     a')
        self.assertEqual(
            crop_or_expand([2], 5, default=[''], scheme='middle'),
            ['', '', 2, '', ''])
        self.assertEqual(
            crop_or_expand('z', 7, scheme='middle'),
            '   z   ')
        self.assertEqual(
            crop_or_expand([3], 4, default=[''], scheme='middle'),
            ['', '', 3, ''])
        self.assertEqual(
            crop_or_expand('y', 8, scheme='middle'),
            '    y   ')
