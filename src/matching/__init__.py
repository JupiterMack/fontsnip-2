# src/matching/__init__.py

"""
Initializes the 'matching' sub-package for the FontSnip application.

This package is the core of the font identification logic. It contains all the
necessary modules for:
1.  Extracting geometric and topological features from character glyphs.
2.  Loading and managing the pre-computed font feature database.
3.  Comparing the features of a captured text snippet against the database to
    find the most likely font matches.

By encapsulating this logic, we can easily swap out or improve the feature
extraction or matching algorithms in the future without affecting other parts
of the application.
"""

# Expose the primary class/function for easier access from other parts of the application.
# This allows other modules to use `from src.matching import FontMatcher`
# instead of the more verbose `from src.matching.matcher import FontMatcher`.
# Note: This assumes a `matcher.py` file with a `FontMatcher` class will be created.
from .matcher import FontMatcher

__all__ = ["FontMatcher"]