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

from junction import Label, Stack, Root

label1 = Label('This label is left aligned')
label2 = Label('This label is centred')
label2.halign = 'center'
label3 = Label('This label is right aligned')
label3.halign = 'right'
label4 = Label(
    'This is a really long label, which should hopefully illustrate that a '
    'label is cropped when it hits the edge of the visible screen, even when '
    'its min_height would allow more of it to fit!')
label4.min_height = 2
label5 = Label('See?')
stack = Stack(label1, label2, label3, label4, label5)
root = Root(stack)
root.run()
