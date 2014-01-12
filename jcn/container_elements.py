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

from abc import abstractmethod, abstractproperty

from .base import ABCUIElement, Block
from .util import weighted_round_robin


class ABCContainerElement(ABCUIElement):
    def __init__(self, *elements, **kwargs):
        self._content = []
        self.active_element = None
        self._root = None
        self._updated = True
        super().__init__(**kwargs)
        for element in elements:
            self.add_element(element)

    def __iter__(self):
        return iter(self._content)

    def __len__(self):
        return len(self._content)

    def __contains__(self, element):
        return element in self._content

    def __getitem__(self, index):
        return self._content[index]

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value
        if self.root:
            self.root.draw()

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, root_element):
        self._root = root_element
        for element in self:
            element.root = root_element

    @property
    def updated(self):
        return self._updated or any(element.updated for element in self)

    @updated.setter
    def updated(self, value):
        self._updated = value
        if value and self.root:
            self.root.update()

    @abstractmethod
    def _get_elements_and_parameters(
            self, width, height, x, y, default_format):
        '''Returns an iterable containing each element with its corresponding
        width, height, x and y position and default_format.
        '''

    def add_element(self, element):
        self._content.append(element)
        if self.active_element is None:
            self.active_element = element
        element.root = self.root
        if self.root:
            self.root.draw()

    def remove_element(self, element):
        self._content.remove(element)
        if element is self.active_element:
            self.active_element = None
        self.updated = True

    def replace_element(self, old_element, new_element):
        i = self._content.index(old_element)
        self._content[i] = new_element
        if old_element is self.active_element:
            self.active_element = new_element
        new_element.root = self.root
        if self.root:
            self.root.draw()

    def _get_all_blocks(
            self, width, height, x=0, y=0, x_crop=None, y_crop=None,
            default_format=None):
        blocks = [Block(x, y, [' ' * width] * height, default_format)]
        x_crop = x_crop or self._halign
        y_crop = y_crop or self._valign
        for element, width, height, x, y, default_format in (
                self._get_elements_and_parameters(
                    width, height, x, y, default_format)):
            blocks.extend(element.get_all_blocks(
                width, height, x, y, x_crop=x_crop, y_crop=y_crop,
                default_format=default_format))
        return blocks

    def _get_updated_blocks(self, default_format):
        blocks = []
        for element in self:
            blocks.extend(element.get_updated_blocks(default_format))
        return blocks

    def handle_input(self, data):
        if self.active_element:
            return self.active_element.handle_input(data)
        else:
            return data


class Box(ABCContainerElement):
    min_width = 2
    min_height = 2

    def __init__(self, content, chars=None, **kwargs):
        super().__init__(content, **kwargs)
        self._top_left = None
        self._top = None
        self._top_right = None
        self._right = None
        self._bottom_right = None
        self._bottom = None
        self._bottom_left = None
        self._left = None
        self.chars = chars

    @property
    def chars(self):
        return ''.join([
            self._top_left, self._top, self._top_right, self._right,
            self._bottom_right, self._bottom, self._bottom_left, self._left])

    @chars.setter
    def chars(self, chars):
        if not chars or len(chars) != 8:
            chars = '+-+|+-+|'
        self._top_left = chars[0]
        self._top = chars[1]
        self._top_right = chars[2]
        self._right = chars[3]
        self._bottom_right = chars[4]
        self._bottom = chars[5]
        self._bottom_left = chars[6]
        self._left = chars[7]
        self.updated = True

    @property
    def max_width(self):
        return self.active_element.max_width + 2

    @property
    def max_height(self):
        return self.active_element.max_height + 2

    def _get_elements_and_parameters(
            self, width, height, x, y, default_format):
        yield (
            self.active_element, width - 2, height - 2, x + 1, y + 1,
            default_format)

    def _get_all_blocks(self, width, height, x=0, y=0, *args, **kwargs):
        blocks = super()._get_all_blocks(width, height, x, y, *args, **kwargs)
        top = [self._top_left + self._top * (width - 2) + self._top_right]
        left = [self._left] * (height - 2)
        bottom = [
            self._bottom_left + self._bottom * (width - 2) +
            self._bottom_right]
        right = [self._right] * (height - 2)
        blocks.extend([
            Block(x, y, top, self.default_format),
            Block(x, y + 1, left, self.default_format),
            Block(x, y + height - 1, bottom, self.default_format),
            Block(x + width - 1, y + 1, right, self.default_format)])
        return blocks


class Stack(ABCContainerElement):
    _possible_valigns = 'top', 'bottom'

    @property
    def min_width(self):
        try:
            return max(
                element.min_width for element in self if element.min_width)
        except ValueError:
            return

    @property
    def min_height(self):
        return sum(element.min_height or 1 for element in self)

    def _get_elements_and_parameters(
            self, width, height, x, y, default_format):
        if self.valign == 'top':
            current_y = y
            for element in self:
                elem_height = min(height, element.min_height or 1)
                if elem_height:
                    yield (
                        element, width, elem_height, x, current_y,
                        default_format)
                    current_y += elem_height
                    height -= elem_height
                else:
                    break
        elif self.valign == 'bottom':
            current_y = y + height
            for element in reversed(self._content):
                elem_height = min(height, element.min_height or 1)
                if elem_height:
                    current_y -= elem_height
                    yield (
                        element, width, elem_height, x, current_y,
                        default_format)
                    height -= elem_height
                else:
                    break


class Zebra(Stack):
    def __init__(self, *args, odd_format=None, even_format=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.odd_format = odd_format
        self.even_format = even_format

    @property
    def _formats(self):
        return [self.even_format, self.odd_format]

    def _get_elements_and_parameters(
            self, width, height, x, y, default_format):
        parent = super()._get_elements_and_parameters(
            width, height, x, y, default_format)
        for i, (element, width, height, x, y, default_format) in enumerate(
                parent):
            zebra_format = self._formats[i % 2]
            if zebra_format:
                if default_format:
                    default_format = default_format + zebra_format
                else:
                    default_format = zebra_format
            yield element, width, height, x, y, default_format


class SplitContainerItemInfo:
    def __init__(self, element, weight, size):
        self.element = element
        self.weight = weight
        self.size = size
        # FIXME: This is a bit of a nasty hack to help the container:
        self._round_robin_additions_to_ignore = size


class SplitContainer(ABCContainerElement):
    _dimension = abstractproperty()

    def __init__(self, *elements, **kwargs):
        self._weights = []
        super().__init__(*elements, **kwargs)
        self._min_width = None
        self._max_width = None
        self._min_height = None
        self._max_height = None

    def add_element(self, element, weight=1):
        self._weights.append(weight)
        super().add_element(element)

    def remove_element(self, element):
        index = self._content.index(element)
        del self._weights[index]
        super().remove_element(element)

    def get_min_size(self, dimension):
        override_min = getattr(self, '_min_' + dimension)
        if override_min:
            return override_min
        mins = [
            e.get_min_size(dimension) for e in self if
            e.get_min_size(dimension) is not None]
        if dimension == self._dimension:
            return sum(mins)
        else:
            return max(mins)

    @property
    def min_width(self):
        return self.get_min_size('width')

    @min_width.setter
    def min_width(self, value):
        self._min_width = value

    @property
    def min_height(self):
        return self.get_min_size('height')

    @min_height.setter
    def min_height(self, value):
        self._min_height = value

    def get_max_size(self, dimension):
        override_max = getattr(self, '_max_' + dimension)
        if override_max:
            return override_max
        maxs = [e.get_max_size(dimension) for e in self]
        if None in maxs:
            return
        if dimension == self._dimension:
            return sum(maxs)
        else:
            return max(maxs)

    @property
    def max_width(self):
        return self.get_max_size('width')

    @max_width.setter
    def max_width(self, value):
        self._max_width = value

    @property
    def max_height(self):
        return self.get_max_size('height')

    @max_height.setter
    def max_height(self, value):
        self._max_height = value

    def _calculate_element_sizes(self, size):
        allocated_size = 0
        item_infos = []
        weighted_items = []
        for element, weight in zip(self, self._weights):
            min_size = element.get_min_size(self._dimension) or 0
            item = SplitContainerItemInfo(element, weight, min_size)
            allocated_size += min_size
            item_infos.append(item)
            weighted_items.append((item, weight))
        for item in weighted_round_robin(weighted_items):
            if allocated_size >= size:
                break
            size_constraint = item.element.get_max_size(self._dimension)
            if size_constraint is None or item.size < size_constraint:
                if item._round_robin_additions_to_ignore:
                    item._round_robin_additions_to_ignore -= 1
                else:
                    item.size += 1
                    allocated_size += 1
        return [(item.element, item.size) for item in item_infos]

    def _get_elements_and_parameters(
            self, width, height, x, y, default_format):
        size = height if self._dimension == 'height' else width
        processed_size = 0
        for element, size in self._calculate_element_sizes(size):
            if self._dimension == 'height':
                yield (
                    element, width, size, x, y + processed_size,
                    default_format)
            else:
                yield (
                    element, size, height, x + processed_size, y,
                    default_format)
            processed_size += size


class HorizontalSplitContainer(SplitContainer):
    _dimension = 'height'


class VerticalSplitContainer(SplitContainer):
    _dimension = 'width'
