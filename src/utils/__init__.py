# src/utils/__init__.py

"""
Initializes the 'utils' sub-package for the FontSnip application.

This package contains miscellaneous utility functions, classes, and constants that are
used across multiple other packages within the application but do not belong to a
specific domain like 'ui', 'processing', or 'matching'.

Potential modules within this package could include:
-   config.py: For managing user settings and application configuration (e.g., hotkeys).
-   paths.py: For resolving paths to application data, system font directories, etc.,
    in a cross-platform manner.
-   singleton.py: A decorator or metaclass for implementing the Singleton design pattern,
    which might be useful for state or database managers.
-   logging_config.py: For setting up a centralized application logger.

By centralizing these utilities, we promote code reuse and maintain a clean, organized
project structure.
"""

# This file can be left empty or can be used to expose functions/classes
# from modules within this package for easier importing from other parts of the app.
# For example:
# from .paths import get_font_dirs, get_app_data_dir
# from .config import ConfigManager
#
# __all__ = ["get_font_dirs", "get_app_data_dir", "ConfigManager"]