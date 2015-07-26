#!/usr/bin/env python

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

        if not isinstance(self.value, (int, long)):
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
        if not isinstance(other, (Address, int, long)):
            raise AddressError('and operation must be performed on another address or an int')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = int(other & self.value)
        return self.__class__(**new_object)

    def __rand__(self, other):
        if not isinstance(other, (Address, int, long)):
            raise AddressError('and operation must be performed on another address or an int')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = int(self.value & other)
        return self.__class__(**new_object)

    def __iand__(self, other):
        self.value = int(other & self)
        return self

    def __or__(self, other):
        if not isinstance(other, (Address, int, long)):
            raise AddressError('or operation must be performed on another address or an int')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = int(other | self.value)
        return self.__class__(**new_object)

    def __ror__(self, other):
        if not isinstance(other, (Address, int, long)):
            raise AddressError('and operation must be performed on another address or an int')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = int(self.value | other)
        return self.__class__(**new_object)

    def __ior__(self, other):
        self.value = int(other | self)
        return self

    def __add__(self, other):
        if not isinstance(other, (int, long)):
            raise AddressError('address objects can only be added with int objects')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = self.value + other
        return self.__class__(**new_object)

    def __radd__(self, other):
        if not isinstance(other, (int, long)):
            raise AddressError('address objects can only be added with int objects')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = other + self.value
        return self.__class__(**new_object)

    def __iadd__(self, other):
        self.value = int(other + self)
        return self

    def __sub__(self, other):
        if not isinstance(other, (int, long)):
            raise AddressError('address objects can only be subtracted by int objects')

        new_object = dict(self.__dict__.items()[:])
        new_object['value'] = self.value - other
        return self.__class__(**new_object)

    def __rsub__(self, other):
        if not isinstance(other, (int, long)):
            raise AddressError('address objects can only be subtracted by int objects')

        new_object = dict(self.__dict__.items()[:])
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
        except AddressError:
            return V6Address.from_string(address)
        except AddressError:
            raise AddressError('could not parse address blindly')

class V4Address(Address):
    MAX = 32
    
    def __str__(self):
        octets = list()
        value = self.value

        for i in xrange(4):
            octets.append(value & 0xFF)
            value >>= 8

        return '.'.join(map(str, octets[::-1]))

    @classmethod
    def from_string(cls, str_val):
        octets = str_val.split('.')

        if len(octets) > 4:
            raise AddressError('string value does not contain 4 or less octets')

        try:
            octets = map(int, octets)
        except ValueError:
            raise AddressError('non-integer found in octets')
        
        octets += [0] * (4 - len(octets))

        if len(filter(lambda x: not (0 <= x <= 255), octets)):
            raise AddressError('string contains octets not in range 0 <= x <= 255')

        value = 0
        
        for octet in octets:
            value <<= 8
            value |= octet

        return cls(value=value)

class V6Address(Address):
    MAX = 128

    def __str__(self):
        sextets = list()
        value = self.value

        for i in xrange(8):
            sextets.append(value & 0xFFFF)
            value >>= 16

        sextets.reverse()
        zero_start = 0
        zero_end = 0
        i = 0

        while i < 8:
            if not sextets[i] == 0:
                i += 1
                continue

            local_start = i
            local_end = local_start
            
            for j in xrange(i+1, 8):
                if not sextets[j] == 0:
                    break

                local_end = j

            if i == j:
                i += 1
            else:
                i = j

            if local_end - local_start > zero_end - zero_start:
                zero_start = local_start
                zero_end = local_end

        if zero_end - zero_start == 0:
            zero_start = -1
            
        result = list()
        i = 0

        while i < 8:
            if i == zero_start:
                if len(result) and result[-1] == ':':
                    result.pop()
                    
                result.append('::')
                i = zero_end+1
                continue

            result.append('%x' % sextets[i])

            i += 1

            if not i == 8:
                result.append(':')
            
        return ''.join(result)

    @classmethod
    def from_string(cls, str_val):
        string_iter = 0
        left_side = list()
        right_side = list()
        all_sides = [left_side, right_side]
        current_side = 0

        eof_state = -1
        numeric_state = 0
        colon_state = 1
        swap_state = 2
        hex_set = '0123456789abcdef'

        current_sextet = -1
        current_state = None

        while string_iter <= len(str_val):
            if not string_iter == len(str_val):
                c = str_val[string_iter].lower()
            else:
                c = None

            if current_state is None:
                current_sextet = -1
                
                if string_iter == len(str_val):
                    current_state = eof_state
                elif c in hex_set:
                    current_sextet = 0
                    current_state = numeric_state
                elif c == ':':
                    current_state = colon_state
                else:
                    raise AddressError('unexpected character in IPv6 string')
            elif current_state == numeric_state:
                if c is None: # hit eof during numeric parsing
                    current_state = eof_state
                elif c in hex_set:
                    current_sextet <<= 4

                    if current_sextet >= 2 ** 16:
                        raise AddressError('sextet contains too many characters')

                    current_sextet |= int(c, 16)
                    string_iter += 1
                elif c == ':':
                    current_state = colon_state
                else:
                    raise AddressError('unexpected character in IPv6 string')
            elif current_state == colon_state:
                if string_iter+1 >= len(str_val):
                    raise AddressError('unexpected termination of IPv6 string')

                next_val = str_val[string_iter]

                if len(left_side + right_side) > 8:
                    raise AddressError('too many sextets in address')

                if current_sextet == -1 and string_iter == 0:
                    pass
                elif not current_sextet == -1:
                    all_sides[current_side].append(current_sextet)
                    current_sextet = -1
                else:
                    raise AddressError('unexpected sextet partition')
                
                if next_val == ':':
                    current_state = swap_state
                else:
                    current_state = None
                
                string_iter += 1
            elif current_state == swap_state:
                if current_side == 1:
                    raise AddressError('IPv6 string can only have one zero padding section')

                string_iter += 1
                current_side += 1
                current_state = None

                if string_iter >= len(str_val):
                    continue
                
                peek = str_val[string_iter]

                if not peek in hex_set:
                    raise AddressError('unexpected delimiter in IPv6 string')
            elif current_state == eof_state:
                if current_sextet == -1:
                    break

                if len(left_side + right_side) > 8:
                    raise AddressError('too many sextets in address')

                all_sides[current_side].append(current_sextet)
                string_iter += 1

        final_sextets = [0]*8

        for sextet in xrange(len(left_side)):
            final_sextets[sextet] = left_side[sextet]

        for sextet in xrange(len(right_side)):
            final_sextets[~sextet] = right_side[~sextet]

        final_value = 0

        for sextet in final_sextets:
            final_value <<= 16
            final_value |= sextet

        return cls(value=final_value)
