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

# coding=utf-8
from unittest import TestCase

from jcn.root import Root
from jcn.display_elements import Fill, Text, Label, ProgressBar
from jcn.formatting import null_placeholder, StringComponent


class TestDisplayElements(TestCase):
    def test_set_get_alignment(self):
        fill = Fill()
        fill.valign = 'middle'
        self.assertEqual(fill.valign, 'middle')
        with self.assertRaises(ValueError):
            fill.valign = 'wrong'
        fill.halign = 'center'
        self.assertEqual(fill.halign, 'center')
        with self.assertRaises(ValueError):
            fill.halign = 'wrong'

    def test_fill(self):
        fill = Fill()
        self.assertEqual(fill._get_lines(10, 0), [])
        self.assertEqual(fill._get_lines(10, 1), ['..........'])
        self.assertEqual(fill._get_lines(2, 2), ['..', '..'])
        self.assertEqual(fill._get_lines(0, 4), ['', '', '', ''])
        fill = Fill('o')
        self.assertEqual(fill._get_lines(1, 1), ['o'])

    def test_text(self):
        content = 'The quick brown fox jumps over the lazy dog'
        text = Text(content)
        expected = [
            'The quick brown  ',
            'fox jumps over   ',
            'the lazy dog     ',
            '                 ']
        self.assertEqual(
            text.get_all_blocks(17, 4)[0].lines, expected)
        text = Text(content, halign='center')
        expected = [
            ' The quick brown ',
            '  fox jumps over ',
            '   the lazy dog  ']
        self.assertEqual(text.get_all_blocks(17, 3)[0].lines, expected)
        text = Text(content, halign='right')
        expected = [
            '  The quick brown fox jumps',
            '          over the lazy dog']
        self.assertEqual(text.get_all_blocks(27, 2)[0].lines, expected)
        text = Text(content, valign='middle')
        expected = [
            ' ' * len(content),
            ' ' * len(content),
            content,
            ' ' * len(content)]
        self.assertEqual(
            text.get_all_blocks(len(content), 4)[0].lines, expected)
        text = Text(content, valign='bottom')
        expected = [
            '                 ',
            'The quick brown  ',
            'fox jumps over   ',
            'the lazy dog     ']
        self.assertEqual(text.get_all_blocks(17, 4)[0].lines, expected)
        text = Text(content, valign='bottom', fillchar='/')
        expected = [
            '/////////////////',
            'The quick brown//',
            'fox jumps over///',
            'the lazy dog/////']
        self.assertEqual(text.get_all_blocks(17, 4)[0].lines, expected)

    def test_text_with_line_breaks(self):
        content = Root.format.underline('Many\nlines ') + 'make\nmuchworkforme'
        text = Text(content)
        expected = [
            Root.format.underline('Many') + '      ',
            Root.format.underline('lines ') + 'make',
            StringComponent(null_placeholder, 'muchworkfo'),
            StringComponent(null_placeholder, 'rme       ')]
        result = text.get_all_blocks(10, 4)[0].lines
        self.assertEqual(result, expected)

    def test_text_with_formatting(self):
        content = (
            Root.format.bold('The ') + 'quick ' + Root.format.red('brown') +
            ' fox ' + Root.format.underline('jumps'))
        text = Text(content)
        expected = [
            (Root.format.bold('The ') + 'quick ' + Root.format.red('brown') +
             '  '),
            ('fox ' + Root.format.underline('jumps') + '        '),
            '                 ',
            '                 ']
        result = text.get_all_blocks(17, 4)[0].lines
        self.assertEqual(result, expected)

    def test_text_with_no_wrap(self):
        text = Text('some long\nstring')
        text.wrap = False
        result = text.get_all_blocks(7, 2)[0].lines
        expected = ['some lo', 'string ']
        self.assertEqual(result, expected)

    def test_label(self):
        label = Label('LHR')
        expected = ['LHR ', '    ']
        self.assertEqual(label.get_all_blocks(4, 2)[0].lines, expected)

    def test_progress_bar(self):
        progress_bar = ProgressBar()
        self.assertEqual(progress_bar._get_lines(3, 1), ['[ ]'])
        self.assertEqual(progress_bar._get_lines(2, 1), ['[ ]'])
        self.assertEqual(progress_bar._get_lines(3, 0), ['[ ]'])
        progress_bar.fraction = 0.5
        self.assertEqual(progress_bar.fraction, 0.5)
        self.assertTrue(progress_bar.updated)
        self.assertEqual(
            progress_bar._get_lines(10, 1), ['[====    ]'])
        progress_bar.fraction = 0.45
        self.assertEqual(
            progress_bar._get_lines(9, 1), ['[===-   ]'])
        progress_bar.fraction = 1
        self.assertEqual(progress_bar._get_lines(9, 1), ['[=======]'])
        progress_bar.fraction = 1.1
        self.assertEqual(progress_bar.fraction, 1)
        progress_bar.fraction = -0.1
        self.assertEqual(progress_bar.fraction, 0)

    def test_progress_bar_unicode(self):
        progress_bar = ProgressBar(':*█:')
        progress_bar.fraction = 0.5
        self.assertEqual(progress_bar._get_lines(8, 1), [':███***:'])

    def test_custom_progress_bar(self):
        progress_bar = ProgressBar('()')
        progress_bar.fraction = 0.5
        self.assertEqual(progress_bar._get_lines(8, 1), ['[===   ]'])
        progress_bar = ProgressBar('(_-)')
        progress_bar.fraction = 0.5
        self.assertEqual(progress_bar._get_lines(8, 1), ['(---___)'])
        progress_bar = ProgressBar('{ `\'"}')
        progress_bar.fraction = 0.45
        self.assertEqual(progress_bar._get_lines(9, 1), ['{"""`   }'])
        progress_bar.fraction = 0.49
        self.assertEqual(progress_bar._get_lines(9, 1), ['{"""\'   }'])
