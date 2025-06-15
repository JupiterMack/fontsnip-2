# src/__init__.py

"""
Initializes the 'src' directory as the main Python package for the FontSnip application.

This package contains all the core source code for the application, including the
GUI, state management, image processing, OCR, and font matching logic. By treating
'src' as a package, we can use clean, relative imports between different modules
of the application.

For example:
- src/main.py
- src/gui/capture_window.py
- src/processing/image_handler.py

From `main.py`, we could import `from .gui.capture_window import CaptureWindow`.
"""

__version__ = "0.1.0"
__author__ = "FontSnip Developer"
__email__ = "developer@example.com"

# This file can be left mostly empty. Its presence is what makes 'src' a package.
# It's good practice to include a docstring and package-level metadata as above.
# No complex application logic or imports should be placed here to avoid circular
# dependencies and to keep the package structure clean and maintainable.