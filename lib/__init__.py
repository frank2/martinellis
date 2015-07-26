#!/usr/bin/env python
def xlongrange(start=None, stop=None):
    if stop is None:
        raise ValueError('no stop point specified')

    if not start is None and stop is None:
        stop = start

    if start is None:
        start = 0

    while start < stop:
        yield start
        start += 1
    
def xrandrange(start=None, stop=None):
    import random

    if start is None and stop is None:
        raise ValueError('no stop point specified')

    if not start is None and stop is None:
        stop = start
        
    if start is None:
        start = 0

    if stop - start <= 0:
        raise ValueError('empty range given')
    
    ranges = [(start, stop)]

    while len(ranges):
        range_tup = ranges.pop(0)

        if len(range_tup) == 1:
            yield range_tup[0]
            continue

        range_start, range_stop = range_tup
        range_value = random.randrange(range_start, range_stop)
        yield range_value

        lower_start = range_start
        lower_stop = range_value

        upper_start = range_value + 1
        upper_stop = range_stop

        if lower_start == range_value:
            if lower_stop == stop:
                stop -= 1
            elif lower_start == upper_stop:
                ranges.insert(0, (lower_start,))
            elif lower_start+1 == upper_stop:
                pass
            else:
                ranges.append((lower_start+1, upper_stop))

            continue
        elif lower_stop-1 == lower_start:
            ranges.insert(0, (lower_start,))
        else:
            ranges.append((lower_start, lower_stop))

        if upper_start >= stop:
            stop -= 1
        elif upper_start == upper_stop:
            pass
        else:
            ranges.append((upper_start, upper_stop))

def randiter(iterable):
    for index in xrandrange(len(iterable)):
        yield iterable[index]

from . import address
from . import cidr

from address import *
from cidr import *

__all__ = ['.', 'randiter', 'xrandrange', 'xlongrange', 'address', 'cidr'
           ,'Address' ,'V4Address', 'V6Address', 'CIDR', 'V4CIDR', 'V6CIDR'
           ,'BaseCIDRSet' ,'ImmutableCIDRSet', 'CIDRSet', 'cset', 'frozencset']
