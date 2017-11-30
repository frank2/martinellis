#!/usr/bin/env python

import copy
import os
import random
import re

from hotmic import randiter, xrandrange

from martinellis import address, xlongrange

class CIDRError(Exception):
    '''
A general error that's raised when errors occur inside :py:class:`CIDR`
objects.'''

    pass

class CIDRSetError(Exception):
    '''
A general error that's raised when errors occur inside :py:class:`CIDRSet`
objects.'''

    pass

class CIDR(object):
    '''
This is the base class for representing IP addresses in CIDR notation. It allows
you to iterate over all addresses within the given network, either sequentially
or randomly. It also gives you the ability to check for network membership of a
given IP address.

Class variables can be changed at the class definition to change the default
behavior of the class. For example, this is how :py:class:`V4CIDR` is
implemented::

   class V4CIDR(CIDR):
       ADDRESS_CLASS = address.V4Address


'''
    
    ADDRESS_CLASS = None
    '''A class type that implements :py:class:`martinellis.address.Address`. An
 exception is raised otherwise.'''
    
    ADDRESS = None
    '''Either an instance of :py:attr:`martinellis.cidr.CIDR.ADDRESS_CLASS` or
a value that can be passed to the *value* argument of its constructor.'''
    
    PREFIX = None
    '''The numerical prefix of the network mask.'''
    
    INCLUSIVE = True
    '''Indicate whether to include the ends of the network. See
:py:func:`martinellis.cidr.CIDR.__init__` for details.'''
    
    RANDOM = False
    '''Indicate whether to iterate over the network randomly.'''
    
    def __init__(self, **kwargs):
        '''
Creates a CIDR object. Keyword arguments are:

   *address_class*: The address class of address objects inside the CIDR object.
   This must implement :py:class:`martinellis.address.Address`.

   *address*: Either an instance of :py:attr:`martinellis.cidr.CIDR.ADDRESS_CLASS`
   or a value that can be passed to the *value* argument of its constructor.

   *prefix*: The network prefix of the given network.

   *cidr*: A string value representing a CIDR-notated network, e.g.: "10.0.0.0/8."
   This can be used in place of the *address* and *prefix* arguments.

   *inclusive*: Indicate whether to include the ends of the network. For example,
   if you have a CIDR of 10.0.0.0/24, setting *inclusive* to **True** would also
   include the addresses 10.0.0.0 and 10.0.0.255 during iteration.

   *random*: Randomize address values on iteration.


'''

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
        '''
Return an :py:class:`martinellis.address.Address` object specified by the member
variable *address_class* representing the netmask of the given network. Example::

   >>> V4CIDR(cidr='10.0.0.0/16').netmask()
   V4Address(255.255.0.0)

'''
        
        return self.address_class.from_prefix(self.prefix)

    def routing_address(self):
        '''
Return an :py:class:`martinellis.address.Address` object specified by the member
variable *address_class* representing the routing address of the given network.
Example::

   >>> V4CIDR(cidr='10.0.0.0/16').routing_address()
   V4Address(10.0.0.0)

'''

        return self.address & self.netmask()

    def broadcast_address(self):
        '''
Return an :py:class:`martinellis.address.Address` object specified by the member
variable *address_class* representing the broadcast address of the given network.
Example::

   >>> V4CIDR(cidr='10.0.0.0/16').broadcast_address()
   V4Address(10.0.255.255)

'''

        return self.address | (self.network_range() - 1)

    def network_range(self):
        '''Return the number of possible addresses in this given network.'''
        
        return 2 ** (self.address.max - self.prefix)

    def get_address(self, index):
        '''Treat the network like an array and get the address at offset *index*.'''
        
        if index < int(not self.inclusive) or index > self.network_range() - int(not self.inclusive):
            raise IndexError('index out of range of network')

        return self.routing_address() + index

    def has_address(self, address_obj):
        '''Check if the given *address_obj* is a member of the network specified
by the :py:class:`martinellis.cidr.CIDR` object. The *address* object must be the
same :py:class:`martinellis.address.Address` object specified by the class's 
*address_class* variable.'''

        if not isinstance(address_obj, address.Address):
            raise CIDRError('can only check for membership of address objects')

        if not issubclass(address_obj.__class__, self.address_class):
            raise CIDRError('address class mismatch')
        
        route_addr = self.routing_address()
        route_cmp = route_addr + int(not self.inclusive)
        broad_addr = self.broadcast_address()
        broad_cmp = broad_addr + int(not self.inclusive)

        return route_cmp <= address_obj <= broad_cmp

    def is_subset_of(self, cidr_obj):
        '''Check if this :py:class:`martinellis.cidr.CIDR` object is a subset of
the given *cidr_obj*.'''

        if not isinstance(cidr_obj, CIDR):
            raise CIDRError('can only check subset of CIDR objects')

        if not issubclass(cidr_obj.address.__class__, self.address_class):
            raise CIDRError('address class mismatch')
        
        route_addr = cidr_obj.routing_address()
        route_cmp = route_addr + int(not cidr_obj.inclusive)
        broad_addr = cidr_obj.broadcast_address()
        broad_cmp = broad_addr + int(not cidr_obj.inclusive)
        
        return self.address & broad_addr == route_addr and self.prefix >= cidr_obj.prefix

    def is_superset_of(self, cidr_obj):
        '''Check if this :py:class:`martinellis.cidr.CIDR` object is a superset of
the given *cidr_obj*.'''

        return cidr_obj.is_subset_of(self)

    def random_address(self):
        '''Return a random address contained within this subnet.'''

        max_index = self.network_range() - int(not self.inclusive)
        random_index = random.randint(1, max_index)
        return self.get_address(random_index)

    def random_subnet(self, prefix=None):
        '''Return a random subnet that's a subset of this subnet.'''
        if prefix is None:
            prefix = random.randint(self.prefix, self.address.max - 1)
        elif prefix <= self.prefix:
            raise ValueError('target subnet would be too large to be contained in this subnet')

        base_address = self.random_address()

        return self.__class__(address=base_address
                              ,prefix=prefix
                              ,inclusive=self.inclusive
                              ,random=self.random)
    
    def __str__(self):
        '''Return a string representation of the CIDR object.'''
        
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
        '''If *other* is a :py:class:`martinellis.cidr.CIDR` object, check if
*other* is a superset of the current object via
:py:func:`martinellis.cidr.CIDR.is_superset_of`. If *other* is an 
:py:class:`martinellis.address.Address` object, check if it is a member of the
network via :py:func:`martinellis.cidr.CIDR.has_address`.'''
        
        if isinstance(other, CIDR):
            return self.is_superset_of(other)
        else:
            return self.has_address(other)

    def __lshift__(self, other):
        '''If *other* is a :py:class:`martinellis.cidr.CIDR` object, check if
*other* is a subset of the current object. If *other* is an
:py:class:`martinellis.address.Address` object, check if it is **not** a member
of the network.'''

        if isinstance(other, CIDR):
            return self.is_subset_of(other)
        else:
            return not self.has_address(other)
        
    def __rrshift__(self, other):
        return self << other

    def __rlshift__(self, other):
        return self >> other
        
    def __len__(self):
        '''Count how many addresses are in this object.'''
        
        return self.network_range() - (int(not self.inclusive) * 2)

    def __getitem__(self, index):
        '''Calls :py:func:`martinellis.cidr.CIDR.get_address`.'''
        
        return self.get_address(index)

    def __iter__(self):
        '''Returns an iterator of addresses within the network. Iteration is
affected by the *random* and *inclusive* switches given to 
:py:func:`martinellis.cidr.CIDR.__init__`.'''
        
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
        '''Check if the *element* is either an address in the network or a subset
network of the :py:class:`martinellis.cidr.CIDR` object.'''
        
        if not isinstance(element, (CIDR, address.Address)):
            raise CIDRError('can only check for membership of CIDR or Address objects')

        return self >> element

    def __copy__(self):
        return self.__class__(**self.__dict__)
    
    @classmethod
    def from_string(cls, cidr):
        '''Convert a CIDR string into a :py:class:`martinellis.cidr.CIDR`
object.'''
        
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
        '''Tries to convert the string into either a
:py:class:`martinellis.cidr.V4CIDR` or a :py:class:`martinellis.cidr.V6CIDR`.
Raises an exception if it can't convert to either.'''
        
        try:
            return V4CIDR.from_string(cidr)
        except address.AddressError:
            return V6CIDR.from_string(cidr)
        except address.AddressError:
            raise CIDRError('could not parse cidr string blindly')

class V4CIDR(CIDR):
    '''A :py:class:`martinellis.cidr.CIDR` class representing an IPv4 CIDR. See
:py:class:`martinellis.cidr.CIDR` for functionality.'''
    
    ADDRESS_CLASS = address.V4Address

class V6CIDR(CIDR):
    '''A :py:class:`martinellis.cidr.CIDR` class representing an IPv6 CIDR. See
:py:class:`martinellis.cidr.CIDR` for functionality.'''
    
    ADDRESS_CLASS = address.V6Address

class CIDRSet(set):
    '''A Python set object representing multiple networks. It's capable of taking
multiple large networks and creating a functional iterator out of them. An
example::

   >>> cidr_set = CIDRSet(V4CIDR(cidr='10.0.0.0/31'), V4CIDR(cidr='10.0.0.50/31'), addresses=True)
   >>> list(cidr_set)
   [V4Address(10.0.0.50), V4Address(10.0.0.51), V4Address(10.0.0.0), V4Address(10.0.0.1)]


'''
    
    INCLUSIVE = False
    '''Same effect as :py:attr:`martinellis.cidr.CIDR.INCLUSIVE`.'''
    
    RANDOM = False
    '''Same effect as :py:attr:`martinellis.cidr.CIDR.RANDOM`.'''

    ADDRESSES = False
    '''Affects what type of value is returned on iteration. See
:py:func:`martinellis.cidr.CIDR.__init__` for details.'''
    
    def __init__(self, *args, **kwargs):
        '''Create a :py:class:`martinellis.cidr.CIDRSet` object. *args* offered
to the constructor are interpretted as the dataset containing
:py:class:`martinellis.cidr.CIDR` objects. The available keyword arguments are:

   *inclusive*: Mark whether the networks are inclusive. See
   :py:func:`martinellis.cidr.CIDR.__init__` for details.

   *random*: Mark whether the networks returned are random.

   *addresses*: If this argument is set to **True**, iteration over the set object
   will return :py:class:`martinellis.address.Address` objects. Otherwise,
   iteration will return :py:class:`martinellis.cidr.CIDR` objects.


'''
        
        self.inclusive = kwargs.setdefault('inclusive', self.INCLUSIVE)
        self.random = kwargs.setdefault('random', self.RANDOM)
        self.addresses = kwargs.setdefault('addresses', self.ADDRESSES)

        set.__init__(self, args)

    def address_length(self):
        '''Return the number of addresses in this set.'''
        
        return sum(map(len, self.network_set()))

    def network_set(self):
        '''Return the set of networks that correspond to this 
:py:class:`martinellis.cidr.CIDRSet` object.'''
        
        return set(super(CIDRSet, self).__iter__())

    def copy(self):
        '''Return a copy of this object.'''
        
        return self.__class__(*self.network_set(), **self.__dict__)

    def add(self, element):
        '''Add a :py:class:`martinellis.cidr.CIDR` object to this set.'''
        
        if not isinstance(element, CIDR):
            raise CIDRSetError('element must be a CIDR object')

        super(CIDRSet, self).add(element)

    def remove(self, element):
        '''Remove a :py:class:`martinellis.cidr.CIDR` object from this set.'''

        if not isinstance(element, CIDR):
            raise CIDRSetError('element must be a CIDR object')

        super(CIDRSet, self).remove(element)

    def discard(self, element):
        '''Remove a :py:class:`martinellis.cidr.CIDR` object from this set only if
it is present.'''
        if not isinstance(element, CIDR):
            raise CIDRSetError('element must be a CIDR object')

        super(CIDRSet, self).discard(element)

    def has_address(self, address_obj):
        '''Check if any element in the set has a given
:py:class:`martinellis.address.Address` object. Essentially calls
:py:func:`martinellis.cidr.CIDR.has_address` on each CIDR in the set.'''

        if not isinstance(address_obj, address.Address):
            raise CIDRSetError('address_obj not an Address object')

        for network in self.network_set():
            if network.has_address(address_obj):
                return True

        return False

    def is_subset_of(self, cidr_obj):
        '''Check if this set of networks is a subset of *cidr_obj*. Essentially
calls :py:func:`martinellis.cidr.CIDR.is_subset_of` on each CIDR in the set.'''

        if not isinstance(cidr_obj, CIDR):
            raise CIDRSetError('cidr_obj should be a CIDR instance')

        for network in self.network_set():
            if not network.is_subset_of(cidr_obj):
                return False

        return True

    def is_superset_of(self, cidr_obj):
        '''Check if this set of networks is a superset of *cidr_obj*. Essentially
calls :py:func:`martinellis.cidr.CIDR.is_superset_of` on each CIDR in the set.'''

        if not isinstance(cidr_obj, CIDR):
            raise CIDRSetError('cidr_obj should be a CIDR instance')

        for network in self.network_set():
            if network.is_superset_of(cidr_obj):
                return True

        return False

    def __copy__(self):
        return self.copy()

    def __lshift__(self, other):
        '''If *other* is an :py:class:`martinellis.address.Address` object, check
if it is not a member of this set of networks. If *other* is a
:py:class:`martinellis.cidr.CIDR` object, check if this set is a subset of
*other*. See :py:func:`martinellis.cidr.CIDRSet.is_subset_of`.'''
        
        if isinstance(other, address.Address):
            return not self.has_address(other)
        elif isinstance(other, cidr.CIDR):
            return self.is_subset_of(other)
        else:
            raise CIDRSetError('other must be a CIDR object or an Address object')

    def __rshift__(self, other):
        '''If *other* is an :py:class:`martinellis.address.Address` object, check
if it is a member of this set of networks. If *other* is a
:py:class:`martinellis.cidr.CIDR` object, check if any network in this set is a
superset of *other*. See :py:func:`martinellis.cidr.CIDRSet.is_superset_of`.'''

        if isinstance(other, address.Address):
            return self.has_address(other)
        elif isinstance(other, cidr.CIDR):
            return self.is_superset_of(other)
        else:
            raise CIDRSetError('other must be a CIDR object or an Address object')

    def __rlshift__(self, other):
        return self >> other

    def __rrshift__(self, other):
        return self << other

    def __contains__(self, other):
        return self >> other

    def __iter__(self):
        '''If *addresses* is set to **True**, return an iterator that iterates
over the addresses contained in the networks. Otherwise, iterate over the networks
themselves. If *random* is set to **True**, return a randomized version of the
configuration.'''
        
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
