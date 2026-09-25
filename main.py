#!/usr/bin/env python3
"""ACCESS root launcher wrapper.
Delegates execution to the ACCESS application in ACCESS/main.py.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCESS_DIR = os.path.join(BASE_DIR, "ACCESS")
if ACCESS_DIR not in sys.path:
    sys.path.insert(0, ACCESS_DIR)

os.chdir(ACCESS_DIR)

if __name__ == "__main__":
    from main import main
    main()
