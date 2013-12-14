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
