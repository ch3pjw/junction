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

from jcn import Root, Fill, VerticalSplitContainer

fill1 = Fill('.')
fill2 = Fill(' ')
fill2.min_width = fill2.max_width = 1
fill3 = Fill(':')
vsplit = VerticalSplitContainer(fill1, fill2, fill3)
root = Root(vsplit)
root.run()