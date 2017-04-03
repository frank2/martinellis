#!/usr/bin/env python

import unittest

from martinellis import *

class TestMartinellis(unittest.TestCase):
    def test_Address(self):
        self.assertEqual(Address.blind_assertion('127.0.0.1').value, 0x7f000001)
        self.assertEqual(Address.blind_assertion('::').value, 0)
        self.assertEqual(Address.blind_assertion('7f00::1').value, 0x7f000000000000000000000000000001L)
    
    def test_CIDR(self):
        pass

if __name__ == '__main__':
    unittest.main()
