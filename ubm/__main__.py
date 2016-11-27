#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Execute with
# $ python neolaneIDE/__main__.py
# $ python -m neolaneIDE

import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of __main__.py
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from ubm.ubm import main

if __name__ == '__main__':
    main()
