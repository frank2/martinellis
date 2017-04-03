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

from martinellis import address
from martinellis import cidr

from martinellis.address import *
from martinellis.cidr import *

__all__ = ['.', 'xlongrange', 'address', 'cidr', 'Address' ,'V4Address',
           'V6Address', 'CIDR', 'V4CIDR', 'V6CIDR', 'CIDRSet']
