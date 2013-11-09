import os
import pep8
from unittest import TestCase


class TestPep8Conformance(TestCase):
    def test_pep8_conformance(self):
        cur_dir_path = os.path.dirname(__file__)
        root_path = os.path.join(cur_dir_path, os.pardir)
        config_path = os.path.join(cur_dir_path, 'pep8_config')
        pep8_style = pep8.StyleGuide(
            paths=[root_path],
            config_file=config_path)
        result = pep8_style.check_files()
        self.assertEqual(
            result.total_errors, 0,
            'Found {:d} code style errors/warnings in {}!'.format(
                result.total_errors, root_path))
