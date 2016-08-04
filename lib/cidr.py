#!/usr/bin/env python

import copy
import os
import random
import re

from . import address
from . import randiter, xrandrange, xlongrange

class CIDRError(Exception):
    pass

class CIDRSetError(Exception):
    pass

class CIDR(object):
    ADDRESS_CLASS = None
    ADDRESS = None
    PREFIX = None
    INCLUSIVE = True
    RANDOM = False
    
    def __init__(self, **kwargs):
        self.address_class = kwargs.setdefault('address_class', self.ADDRESS_CLASS)

        if self.address_class is None:
            raise CIDRError('address_class undefined')

        if not issubclass(self.address_class, address.Address):
            raise CIDRError('address_class must implement Address')
        
        if 'cidr' in kwargs:
            new_object = self.__class__.from_string(kwargs['cidr'])
            kwargs['address'] = new_object.address
            kwargs['prefix'] = new_object.prefix

        self.address = kwargs.setdefault('address', self.ADDRESS)
        self.prefix = kwargs.setdefault('prefix', self.PREFIX)
        self.inclusive = kwargs.setdefault('inclusive', self.INCLUSIVE)
        self.random = kwargs.setdefault('random', self.RANDOM)

        if self.address is None:
            raise CIDRError('no base address provided')
        
        if isinstance(self.address, str):
            self.address = self.address_class.from_string(self.address)

        if not isinstance(self.address, self.address_class):
            raise CIDRError('address must be an instance of the address class')

        if self.prefix is None:
            raise CIDRError('no network prefix provided')

        if not isinstance(self.prefix, int):
            raise CIDRError('prefix must be an integer')

    def netmask(self):
        return self.address_class.from_prefix(self.prefix)

    def routing_address(self):
        return self.address & self.netmask()

    def broadcast_address(self):
        return self.address | (self.network_range() - 1)

    def network_range(self):
        return 2 ** (self.address.max - self.prefix)

    def get_address(self, index):
        if index < int(not self.inclusive) or index > self.network_range() - int(not self.inclusive):
            raise IndexError('index out of range of network')

        return self.routing_address() + index
    
    def __str__(self):
        return '%s/%s' % (self.routing_address(), self.prefix)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def __hash__(self):
        return hash('%d/%d/%d/%d' % (hash(self.address), self.prefix, int(self.inclusive), int(self.random)))

    def __cmp__(self, other):
        if not isinstance(other, CIDR):
            raise CIDRError('cannot compare CIDR object to non-CIDR objects')

        if not self.address.max == other.address.max:
            return cmp(self.address.max, other.address.max)
        
        if not self.prefix == other.prefix:
            return cmp(self.prefix, other.prefix)

        return cmp(self.address, other.address)

    def __rshift__(self, other):
        if not isinstance(other, (CIDR, address.Address)):
            raise CIDRError('can only compare to other CIDR objects or Address objects')
        route_addr = self.routing_address()
        route_cmp = route_addr + int(not self.inclusive)
        broad_addr = self.broadcast_address()
        broad_cmp = broad_addr + int(not self.inclusive)

        if isinstance(other, address.Address):
            return route_cmp <= other <= broad_cmp
        else:
            return other.address & broad_addr == route_addr and other.prefix >= self.prefix

    def __lshift__(self, other):
        if not isinstance(other, (CIDR, address.Address)):
            raise CIDRError('can only compare to other CIDR objects or Address objects')

        route_addr = self.routing_address()
        route_cmp = route_addr + int(not self.inclusive)
        broad_addr = self.broadcast_address()
        broad_cmp = broad_addr + int(not self.inclusive)

        if isinstance(other, address.Address):
            return other < route_cmp or other > broad_cmp
        else:
            return not other.address & broad_addr == route_addr or other.prefix < self.prefix
        
    def __rrshift__(self, other):
        return self << other

    def __rlshift__(self, other):
        return self >> other
        
    def __len__(self):
        return self.network_range() - (int(not self.inclusive) * 2)

    def __getitem__(self, index):
        return self.get_address(index)

    def __iter__(self):
        upper_address = self.network_range()
        lower_address = 0

        upper_address -= int(not self.inclusive)
        lower_address += int(not self.inclusive)
        
        if not self.inclusive:
            upper_address += 1
            lower_address += 1

        if self.random:
            addresses = xrandrange(lower_address, upper_address)
        else:
            addresses = xlongrange(lower_address, upper_address)

        for address_obj in addresses:
            yield self[address_obj]

    def __contains__(self, element):
        if not isinstance(element, (CIDR, address.Address)):
            raise CIDRError('can only check for membership of CIDR or Address objects')

        return self >> element

    def __copy__(self):
        return self.__class__(**self.__dict__)
    
    @classmethod
    def from_string(cls, cidr):
        address_class = getattr(cls, 'ADDRESS_CLASS', None)

        if address_class is None:
            raise CIDRError('cidr class has no static address class')

        if not issubclass(address_class, address.Address):
            raise CIDRError('address class does not implement Address')
        
        split_cidr = cidr.split('/')

        if len(split_cidr) > 2:
            raise CIDRError('too many prefixes in CIDR string')

        address_obj = address_class.from_string(split_cidr.pop(0))
        
        if not len(split_cidr):
            prefix = getattr(address_class, 'MAX', None)

            if prefix is None:
                raise CIDRError('address class provides no maximum bitrange')
        else:
            prefix = split_cidr.pop()

        kwargs = dict()
        kwargs['address'] = address_obj
        kwargs['prefix'] = int(prefix)
        kwargs['inclusive'] = cls.INCLUSIVE
        kwargs['random'] = cls.RANDOM

        return cls(**kwargs)

    @staticmethod
    def blind_assertion(cidr):
        try:
            return V4CIDR.from_string(cidr)
        except address.AddressError:
            return V6CIDR.from_string(cidr)
        except address.AddressError:
            raise CIDRError('could not parse cidr string blindly')

class V4CIDR(CIDR):
    ADDRESS_CLASS = address.V4Address

class V6CIDR(CIDR):
    ADDRESS_CLASS = address.V6Address

class CIDRSet(set):
    INCLUSIVE = False
    RANDOM = False
    ADDRESSES = False
    
    def __init__(self, *args, **kwargs):
        self.inclusive = kwargs.setdefault('inclusive', self.INCLUSIVE)
        self.random = kwargs.setdefault('random', self.RANDOM)
        self.addresses = kwargs.setdefault('addresses', self.ADDRESSES)

        set.__init__(self, args)

    def address_length(self):
        return sum(map(len, self.network_set()))

    def network_set(self):
        return set(super(CIDRSet, self).__iter__())

    def copy(self):
        return self.__class__(*self.network_set(), **self.__dict__)

    def add(self, element):
        if not isinstance(element, CIDR):
            raise CIDRSetError('element must be a CIDR object')

        super(CIDRSet, self).add(element)

    def remove(self, element):
        if not isinstance(element, CIDR):
            raise CIDRSetError('element must be a CIDR object')

        super(CIDRSet, self).remove(element)

    def discard(self, element):
        if not isinstance(element, CIDR):
            raise CIDRSetError('element must be a CIDR object')

        super(CIDRSet, self).discard(element)

    def __copy__(self):
        return self.copy()

    def __lshift__(self, other):
        if not isinstance(other, (address.Address, CIDR)):
            raise CIDRSetError('can only get membership of Address or CIDR types')
        
        return len([x for x in self.network_set() if x << other]) > 0

    def __rshift__(self, other):
        if not isinstance(other, (address.Address, CIDR)):
            raise CIDRSetError('can only get membership of Address or CIDR types')
        
        return len([x for x in self.network_set() if x >> other]) > 0

    def __rlshift__(self, other):
        return self >> other

    def __rrshift__(self, other):
        return self << other

    def __iter__(self):
        networks = list(self.network_set())
        
        if self.random:
            random.shuffle(networks)

        if not self.addresses:
            for network in networks:
                yield network

            raise StopIteration

        if self.random:
            network_iterators = list(map(randiter, networks))
        else:
            network_iterators = list(map(iter, networks))

        while len(network_iterators):
            if not self.random:
                iterator = network_iterators.pop(0)

                for address in iterator:
                    yield address

                continue
            
            index = random.randrange(0, len(network_iterators))
            iterator = network_iterators[index]

            try:
                yield next(iterator)
            except StopIteration:
                network_iterators.pop(index)
                continue
