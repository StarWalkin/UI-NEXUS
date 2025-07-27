#!/usr/bin/env python3
"""Direct runner for emulator initialization.

This script can be run directly to initialize the emulator:
    python -m emulator_init.run --config_path=config.json
"""

if __name__ == '__main__':
    from .cli import run_cli
    run_cli() 