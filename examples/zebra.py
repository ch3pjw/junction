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

from junction import Root, Text, Zebra, Terminal

text1 = Text('Some interesting text might go here')
text2 = Text('The Zebra will help you differentiate lines')
text3 = Text('A third line will help the logic become clearer')
text3.min_height = 2
content = [text1, text2, text3] * 10
term = Terminal()
zebra = Zebra(*content, odd_format=Root.format.on_color(235))
root = Root(zebra)
root.run()
