# Copyright (C) 2013 Paul Weaver <p.weaver@ruthorn.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

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
