#!/usr/bin/env python

def xlongrange(start=None, stop=None):
    '''
Creates a range iterator similar to xrange, but for large numbers. Works
pretty much like the range() function, in that it generates a range from 
0 -> *start* non-inclusive if *stop* is not specified, or *start* -> *stop*
non-inclusive if it is.'''
    
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
    '''
Produces an iterator similiar to xrange with the interface of range. 
The iterator yields random numbers from 0 <= x < *start* if *stop* is not
specified, or *start* <= x < *stop* if it is. Here's an example of xrandrange::

   >>> list(xrandrange(10))
   [2, 1, 0, 7, 4, 3, 8, 5, 9, 6]
   >>> list(xrandrange(10, 20))
   [11, 10, 16, 13, 12, 17, 14, 18, 15, 19]


'''
    
    import random

    if start is None and stop is None:
        raise ValueError('no stop point specified')

    if not start is None and stop is None:
        stop = start
        start = 0
        
    if start is None:
        start = 0

    if stop - start <= 0:
        raise ValueError('empty range given')
    
    ranges = [(start, stop)]

    while len(ranges):
        range_tup = ranges.pop(0)
        range_input = None

        if len(range_tup) == 1:
            range_value = range_tup[0]
        else:
            range_value = random.randrange(*range_tup)

        range_input = yield range_value

        if range_input is None:
            pass
        elif not isinstance(range_input, tuple):
            raise ValueError('input to xrandrange must be a tuple of numbers')
        else:
            if len(range_input) == 1:
                ranges.insert(0, range_input)
            else:
                ranges.append(range_input)

        if len(range_tup) == 1:
            continue

        range_start, range_stop = range_tup
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
    '''
Create an iterator that yields random elements from the iterable object 
*iterable*.'''
    
    send_queue = list()
    iter_len = len(iterable)
    iter_range = xrandrange(iter_len)

    while 1:
        if len(send_queue):
            receive = yield send_queue.pop()

            if not receive is None:
                send_queue.append(receive)

            continue
                
        if not len(iterable) == iter_len:
            new_iter_len = len(iterable)
            iter_value = iter_range.send((iter_len, new_iter_len))
            iter_len = new_iter_len
        else:
            iter_value = next(iter_range)
            
        receive = yield iterable[iter_value]

        if not receive is None:
            send_queue.append(receive)

from martinellis import address
from martinellis import cidr

from martinellis.address import *
from martinellis.cidr import *

__all__ = ['.', 'randiter', 'xrandrange', 'xlongrange', 'address', 'cidr'
           ,'Address' ,'V4Address', 'V6Address', 'CIDR', 'V4CIDR', 'V6CIDR'
           ,'CIDRSet']
