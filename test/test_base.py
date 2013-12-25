from unittest import TestCase

from junction.base import ABCUIElement


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
