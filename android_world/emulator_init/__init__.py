"""Android Emulator Initialization Package.

This package provides tools to initialize Android emulator state based on
configuration JSON files. It supports configuring various apps and system
settings to set up the emulator for specific tasks or tests.
"""

from .core import EmulatorInitializer

__version__ = "1.0.0"
__all__ = ["EmulatorInitializer"] 