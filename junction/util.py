from enum import Enum, unique
from itertools import cycle


@unique
class VAlign(Enum):
    top = 1
    middle = 2
    bottom = 3


@unique
class HAlign(Enum):
    left = 1
    center = 2
    right = 3


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


def fixed_length_list(l, length, default='', valign=VAlign.top):
    '''Takes a list and returns a list of elements from that list that is
    at most length element long. If the original list is too long, elements are
    dropped, if it is too short, elements of default value are added as
    required.

    :parameter l: the list to limit/pad.
    :parameter length: the length to limit/pad to.
    :parameter default: the default value to use for list elements, should the
        list require padding.
    :parameter valign: Which end of the list data should be shunted to if it is
        too short. We use valign, because in junction, we are using lists for
        lines of text.
    '''
    result = [i for i in l][:length]
    if len(l) < length:
        missing = length - len(l)
        if valign is VAlign.top:
            result.extend([default] * missing)
        elif valign is VAlign.bottom:
            result[0:0] = [default] * missing
        elif valign is VAlign.middle:
            result[0:0] = [default] * (missing // 2)
            result.extend([default] * ((missing + 1) // 2))
    return result
