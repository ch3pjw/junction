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

import asyncio
from itertools import cycle


def clamp(value, min_=None, max_=None):
    if min_ is None and max_ is None:
        return value
    if min_ is None:
        min_ = min(value, max_)
    if max_ is None:
        max_ = max(value, min_)
    return sorted((value, min_, max_))[1]


def crop_or_expand(iterable, length, default=' ', scheme='beginning'):
    if len(iterable) > length:
        # Crop:
        if scheme == 'beginning':
            result = iterable[:length]
        elif scheme == 'middle':
            extra = len(iterable) - length
            result = iterable[extra // 2:-extra // 2]
        elif scheme == 'end':
            result = iterable[-length:]
    elif len(iterable) < length:
        # Expand:
        missing = length - len(iterable)
        try:
            if scheme == 'beginning':
                result = iterable + default * missing
            elif scheme == 'middle':
                result = (default * ((missing + 1) // 2) +
                          iterable +
                          default * (missing // 2))
            elif scheme == 'end':
                result = default * missing + iterable
        except TypeError:
            raise TypeError(
                "Can't expand the given iterable of type {!r} with default "
                "value of type {!r}".format(type(iterable), type(default)))
    else:
        # Perfect :-)
        result = iterable[:]
    return result


def weighted_round_robin(iterable):
    '''Takes an iterable of tuples of <item>, <weight> and cycles around them,
    returning heavier (integer) weighted items more frequently.
    '''
    cyclable_list = []
    assigned_weight = 0
    still_to_process = [
        (item, weight) for item, weight in
        sorted(iterable, key=lambda tup: tup[1], reverse=True)]
    while still_to_process:
        for i, (item, weight) in enumerate(still_to_process):
            if weight > assigned_weight:
                cyclable_list.append(item)
            else:
                del still_to_process[i]
        assigned_weight += 1
    return cycle(cyclable_list)


class LoopingCall:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.interval = None
        self.loop = None
        self.running = False

    def start(self, interval, loop=None):
        self.interval = interval
        self.loop = loop or asyncio.get_event_loop()
        self.running = True
        self._execute()

    def _execute(self):
        if self.running:
            self.func(*self.args, **self.kwargs)
            self.loop.call_later(self.interval, self._execute)

    def stop(self):
        self.running = False


class InheritDocstrings(type):
    def __new__(cls, cls_name, bases, classdict):
        for attr_name, attr in classdict.items():
            if getattr(attr, '__doc__') is None:
                # See if this attribute came from any of our ancestors
                for base in bases:
                    if attr_name in base.__dict__:
                        attr.__doc__ = base.__dict__[attr_name].__doc__
                        break
        return super().__new__(cls, cls_name, bases, classdict)
