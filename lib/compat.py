#!/usr/bin/env python

try: #python2
    import __builtin__
    
    int = int
    long = long
    str = str
    unicode = unicode
    env = 2
except ImportError: #python3
    import builtins

    int = int
    long = int
    str = str
    unicode = str
    env = 3

__all__ = ['int', 'long', 'str', 'unicode', 'env']
