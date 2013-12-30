#! /usr/bin/env python

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

from __future__ import division
import nose
import coverage
import os
import sys
import blessings

term = blessings.Terminal()

this_dir = os.path.dirname(os.path.abspath(__file__))

c = coverage.coverage()
c.start()
nose.run(defaultTest=os.path.join(this_dir, 'test'))
c.stop()

analysis = []
for cur_dir, sub_dir, file_names in os.walk(
        os.path.join(this_dir, 'jcn')):
    for file_name in file_names:
        file_name = os.path.join(cur_dir, file_name)
        if file_name.endswith('.py'):
            fn, executable, not_run, missing_lines_str = c.analysis(file_name)
            analysis.append((len(executable), len(not_run)))

executable = 0
run = 0
for e, r in analysis:
    executable += e
    run += e - r

total_coverage = 100 * run / executable

coverage_file_name = os.path.join(this_dir, 'test', 'total_coverage')

try:
    with open(coverage_file_name) as fp:
        previous_coverage = float(fp.read())
except IOError:
    previous_coverage = 100
    term.stream.write(
        'Could not find previous coverage metric, set to {}%\n'.format(
            previous_coverage))

with open(coverage_file_name, 'w') as fp:
    fp.write(str(total_coverage))

if round(total_coverage, 2) >= round(previous_coverage, 2):
    message = '\nUnit test code coverage was {}{:.1f}%\n'.format(
        term.bright_green, total_coverage)
    term.stream.write(message)
    exit_code = 0
else:
    message = (
        '\nUnit test coverage decreased from {:.1f}% to {}{:.1f}%!\n'.format(
            previous_coverage, term.bright_red, total_coverage))
    term.stream.write(message)
    exit_code = 1

term.stream.write(term.normal)
sys.exit(exit_code)
