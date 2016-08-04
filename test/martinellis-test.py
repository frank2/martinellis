#!/usr/bin/env python

from martinellis import *

def test_randiter():
    iterable = range(20)
    iter_set = set(iterable)
    rand_list = list(randiter(iterable))

    assert not rand_list == iterable
    assert set(list(randiter(iterable))) == iter_set
    print '[randiter: PASS]'

def test_Address():
    assert Address.blind_assertion('127.0.0.1').value == 0x7f000001
    assert Address.blind_assertion('::').value == 0
    assert Address.blind_assertion('7f00::1').value == 0x7f000000000000000000000000000001L
    
def test_CIDR():
    pass

if __name__ == '__main__':
    test_randiter()
    test_Address()
    test_CIDR()
