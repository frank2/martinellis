#!/usr/bin/env python

import socket
import struct

class AddressError(Exception):
    '''
A general error that's raised when errors occur inside :py:class:`Address` 
objects.'''
    
    pass

class Address(object):
    '''
This is the base class for handling IPv4 and IPv6 objects. It can handle arbitrary
IP sizes if you really want that for some reason, but generally you don't want to 
use this class. You *probably* want :py:class:`V4Address` or :py:class:`V6Address`
instead. This just contains all the basic address functionality you need.

Class variables can be changed at the class definition to change the default
behavior of the class. For example, this is how :py:class:`V4Address` is
implemented::

   class V4Address(Address):
       MAX = 32


'''
    
    MAX = None
    '''The size of the integer, in bits, representing the IP address.'''
    
    VALUE = None
    '''The integer or string value of the IP address being represented.'''
    
    def __init__(self, **kwargs):
        '''
Creates an address object. Keyword arguments are:

   *value*: The integer or string value of the IP address being represented.

   *max*: The size of the integer, in bits, representing the IP address.


'''
        
        self.value = kwargs.setdefault('value', self.VALUE)
        self.max = kwargs.setdefault('max', self.MAX)

        if self.value is None:
            raise AddressError('a value must be provided')

        if self.max is None:
            raise AddressError('a maximum bitrange must be provided')

        if isinstance(self.value, str):
            addr_obj = self.__class__.from_string(self.value)
            
            self.value = addr_obj.value
            self.max = addr_obj.max
        elif not float(self.value).is_integer():
            raise AddressError('value must be an integer or string')

    def __int__(self):
        '''Return the integer representation of the IP address.'''
        
        return self.value
    
    def __hash__(self):
        return hash('%d/%d' % (self.value, self.max))

    def __cmp__(self, other):
        if not isinstance(other, Address):
            raise AddressError('comparative operation not possible with non-Address')

        if not self.max == other.max:
            return cmp(self.max, other.max)

        return cmp(self.value, other.value)

    def __and__(self, other):
        '''
Perform a binary AND operation on an IP address with either another
:py:class:`Address` object or another integer. Examples::

   >>> V4Address(value='10.20.30.40') & 0xFFFFFF00
   V4Address(10.20.30.0)
   >>> V4Address(value='10.20.30.40') & V4Address(value='255.255.240.0')
   V4Address(10.20.16.0)


'''

        if not isinstance(other, Address) and not float(other).is_integer():
            raise AddressError('and operation must be performed on another address or an int')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = int(other & self.value)
        return self.__class__(**new_object)

    def __rand__(self, other):
        if not isinstance(other, (Address, int)):
            raise AddressError('and operation must be performed on another address or an int')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = int(self.value & other)
        return self.__class__(**new_object)

    def __iand__(self, other):
        self.value = int(other & self)
        return self

    def __or__(self, other):
        '''Perform a binary OR operation on the address with an 
:py:class:`Address` object or another integer.'''
        
        if not isinstance(other, (Address, int)):
            raise AddressError('or operation must be performed on another address or an int')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = int(other | self.value)
        return self.__class__(**new_object)

    def __ror__(self, other):
        if not isinstance(other, (Address, int)):
            raise AddressError('and operation must be performed on another address or an int')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = int(self.value | other)
        return self.__class__(**new_object)

    def __ior__(self, other):
        self.value = int(other | self)
        return self

    def __add__(self, other):
        '''
Add an integer to the given IP address. Example::

   >>> V4Address(value='10.20.30.40') + 5
   V4Address(10.20.30.45)


'''
        
        if not isinstance(other, int):
            raise AddressError('address objects can only be added with int objects')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = self.value + other
        return self.__class__(**new_object)

    def __radd__(self, other):
        if not isinstance(other, int):
            raise AddressError('address objects can only be added with int objects')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = other + self.value
        return self.__class__(**new_object)

    def __iadd__(self, other):
        self.value = int(other + self)
        return self

    def __sub__(self, other):
        '''
Subtract an integer from the given IP address. Example::

   >>> V4Address(value='10.20.30.40') - 5
   V4Address(10.20.30.35)


'''
        
        if not isinstance(other, int):
            raise AddressError('address objects can only be subtracted by int objects')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = self.value - other
        return self.__class__(**new_object)

    def __rsub__(self, other):
        if not isinstance(other, int):
            raise AddressError('address objects can only be subtracted by int objects')

        new_object = dict(list(self.__dict__.items())[:])
        new_object['value'] = other - self.value
        return self.__class__(**new_object)

    def __isub__(self, other):
        self.value = int(self - other)
        return self

    def __str__(self):
        '''Convert an :py:class:`Address` object into a string.'''
        
        raise AddressError('__str__ not implemented')

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def __copy__(self):
        return self.__class__(**self.__dict__)

    @classmethod
    def from_string(cls, str_val):
        '''Convert a string representation of an IP address into an
:py:class:`Address` object.'''
        
        raise AddressError('from_string not implemented')

    @classmethod
    def from_prefix(cls, prefix):
        '''
Creates an IP address from a given bitmask. Example::

   >>> V4Address.from_prefix(24)
   V4Address(255.255.255.0)

'''
        
        bitmax = getattr(cls, 'MAX', None)

        if bitmax is None:
            raise AddressError('class has no maximum bit range set')
        
        shift = bitmax - prefix
        value = ((2 ** prefix) - 1) << shift

        return cls(value=value)

    @staticmethod
    def blind_assertion(address):
        '''Tries to convert the string address into either a 
:py:class:`V4Address` or a :py:class:`V6Address`. Raises an exception if it
can't convert to either.'''
        
        try:
            return V4Address.from_string(address)
        except (AddressError, socket.error):
            return V6Address.from_string(address)
        except (AddressError, socket.error):
            raise AddressError('could not parse address blindly')

class V4Address(Address):
    '''An :py:class:`Address` class representing an IPv4 address. See
:py:class:`Address` for functionality.'''
    
    MAX = 32
    
    def __str__(self):
        struct_data = struct.pack('>L', self.value)
        return socket.inet_ntop(socket.AF_INET, struct_data)

    @classmethod
    def from_string(cls, str_val):
        try:
            struct_data = socket.inet_pton(socket.AF_INET, str_val)
        except (OSError, socket.error):
            raise AddressError('inet_pton failed')

        int_data = struct.unpack('>L', struct_data)[0]

        return cls(value=int_data)

class V6Address(Address):
    '''An :py:class:`Address` class representing an IPv6 address. See
:py:class:`Address` for functionality.'''
    
    MAX = 128

    def __str__(self):
        struct_data = struct.pack('>QQ'
                                  ,self.value >> 64
                                  ,self.value & ((2 ** 64) - 1))
        return socket.inet_ntop(socket.AF_INET6, struct_data)

    @classmethod
    def from_string(cls, str_val):
        try:
            struct_data = socket.inet_pton(socket.AF_INET6, str_val)
        except (OSError, socket.error):
            raise AddressError('inet_pton failed')

        int_data = struct.unpack('>QQ', struct_data)
        lhs, rhs = int_data
        return cls(value=lhs << 64 | rhs)
