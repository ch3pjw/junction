from itertools import cycle


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
