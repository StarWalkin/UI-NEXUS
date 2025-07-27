#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import emulator_init as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

if __name__ == '__main__':
    from emulator_init.cli import run_cli
    run_cli() 