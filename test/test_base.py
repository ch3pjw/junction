from unittest import TestCase

from junction.base import ABCUIElement, Block


class TestABCUIElement(TestCase):
    def test_repr(self):
        class MyElement(ABCUIElement):
            def _get_all_blocks(self, *args, **kwargs):
                pass

            def _get_updated_blocks(self, *args, **kwargs):
                pass
        my_element = MyElement()
        self.assertIn('MyElement element', repr(my_element))
        my_element = MyElement(name='testing')
        self.assertIn('MyElement element', repr(my_element))
        self.assertIn('testing', repr(my_element))


class TestBlock(TestCase):
    def test_repr(self):
        block = Block(1, 2, ['hello', 'world'], None)
        self.assertEqual(repr(block), "Block(1, 2, ['hello', 'world'])")
        block = Block(3, 4, ['Milton', 'Jones'], 'spangly')
        self.assertEqual(
            repr(block), "Block(3, 4, ['Milton', 'Jones'], 'spangly')")
