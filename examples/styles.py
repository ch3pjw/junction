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

from jcn import Root, Text


Root.style.heading = Root.format.underline
Root.style.h1 = Root.style.heading + Root.format.bold
Root.style.h2 = Root.style.heading + Root.format.color(240)

text = Text(
    Root.style.h1('Disclaimer:\n') +
    "This software comes with absolutely no warranty, not even for "
    "merchantability or fitness for a particular purpose\n\n" +
    Root.style.h2('Footnote:\n') +
    "But we've made every effort to make it awesome ;-)")
root = Root(text)
root.run()
