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
        if not isinstance(default, type(iterable)):
            # Duck-typing is good, but we're trying to avoid some hard-to-debug
            # messages more.
            raise TypeError(
                "Can't crop or expand the given iterable of type {!r} with "
                "default value of type {!r}".format(
                    type(iterable), type(default)))
        missing = length - len(iterable)
        if scheme == 'beginning':
            result = iterable + default * missing
        elif scheme == 'middle':
            result = (default * ((missing + 1) // 2) +
                      iterable +
                      default * (missing // 2))
        elif scheme == 'end':
            result = default * missing + iterable
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
