#!/usr/bin/env python

import socket
import struct

class AddressError(Exception):
    pass

class Address:
    MAX = None
    VALUE = None
    
    def __init__(self, **kwargs):
        self.value = kwargs.setdefault('value', self.VALUE)
        self.max = kwargs.setdefault('max', self.MAX)

        if self.value is None:
            raise AddressError('a value must be provided')

        if self.max is None:
            raise AddressError('a maximum bitrange must be provided')

        if not isinstance(self.value, int):
            raise AddressError('value must be an integer')

    def __int__(self):
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
        if not isinstance(other, (Address, int)):
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
        raise AddressError('__str__ not implemented')

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def __copy__(self):
        return self.__class__(**self.__dict__)

    @classmethod
    def from_string(cls, str_val):
        raise AddressError('from_string not implemented')

    @classmethod
    def from_prefix(cls, prefix):
        bitmax = getattr(cls, 'MAX', None)

        if bitmax is None:
            raise AddressError('class has no maximum bit range set')
        
        shift = bitmax - prefix
        value = ((2 ** prefix) - 1) << shift

        return cls(value=value)

    @staticmethod
    def blind_assertion(address):
        try:
            return V4Address.from_string(address)
        except (AddressError, socket.error):
            return V6Address.from_string(address)
        except (AddressError, socket.error):
            raise AddressError('could not parse address blindly')

class V4Address(Address):
    MAX = 32
    
    def __str__(self):
        struct_data = struct.pack('>L', self.value)
        return socket.inet_ntop(socket.AF_INET, struct_data)

    @classmethod
    def from_string(cls, str_val):
        struct_data = socket.inet_pton(socket.AF_INET, str_val)
        int_data = struct.unpack('>L', struct_data)[0]

        return cls(value=int_data)

class V6Address(Address):
    MAX = 128

    def __str__(self):
        struct_data = struct.pack('>QQ'
                                  ,self.value >> 64
                                  ,self.value & ((2 ** 64) - 1))
        return socket.inet_ntop(socket.AF_INET6, struct_data)

    @classmethod
    def from_string(cls, str_val):
        struct_data = socket.inet_pton(socket.AF_INET6, str_val)
        int_data = struct.unpack('>QQ', struct_data)
        lhs, rhs = int_data
        return cls(value=lhs << 64 | rhs)
