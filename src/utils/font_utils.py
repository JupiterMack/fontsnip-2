# src/utils/font_utils.py

"""
Utility functions for finding system font files.

This module provides cross-platform functions to locate font directories and
discover all available .ttf and .otf font files on the user's system. This is
essential for the pre-computation script that builds the font feature database.
"""

import os
import sys
from pathlib import Path
from typing import List, Set

# Define common font file extensions
FONT_EXTENSIONS = {".ttf", ".otf"}


def get_system_font_dirs() -> List[Path]:
    """
    Identifies and returns a list of common font directories for the current OS.

    This function is cross-platform and checks for standard font locations on
    Windows, macOS, and Linux. It only returns directories that actually exist.

    Returns:
        A list of Path objects pointing to existing font directories.
    """
    font_dirs: List[Path] = []
    home = Path.home()

    if sys.platform == "win32":
        # Windows: C:\Windows\Fonts and user-specific fonts
        system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
        font_dirs.append(system_root / "Fonts")

        # User-specific fonts are in %LOCALAPPDATA%\Microsoft\Windows\Fonts
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            font_dirs.append(Path(local_app_data) / "Microsoft/Windows/Fonts")

    elif sys.platform == "darwin":
        # macOS: /System/Library/Fonts, /Library/Fonts, ~/Library/Fonts
        font_dirs.extend([
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            home / "Library/Fonts"
        ])

    elif sys.platform.startswith("linux"):
        # Linux: /usr/share/fonts, /usr/local/share/fonts, ~/.fonts, ~/.local/share/fonts
        font_dirs.extend([
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            home / ".fonts",
            home / ".local/share/fonts"
        ])

    # Return only the directories that actually exist on the system
    return [d for d in font_dirs if d.exists() and d.is_dir()]


def find_font_files(directories: List[Path] = None) -> List[str]:
    """
    Recursively finds all font files (.ttf, .otf) in the given directories.

    If no directories are provided, it will use the system's default font
    directories as discovered by `get_system_font_dirs`.

    Args:
        directories: An optional list of Path objects for directories to search.

    Returns:
        A sorted list of unique, absolute string paths to all found font files.
    """
    if directories is None:
        search_dirs = get_system_font_dirs()
    else:
        search_dirs = directories

    found_fonts: Set[str] = set()

    for dir_path in search_dirs:
        if not dir_path.exists():
            continue

        # Use rglob to recursively find all files with the specified extensions
        for ext in FONT_EXTENSIONS:
            # Case-insensitive search by checking both lower and upper case extensions
            for pattern in (f"*{ext.lower()}", f"*{ext.upper()}"):
                for font_file in dir_path.rglob(pattern):
                    if font_file.is_file():
                        # Store the absolute, resolved path as a string to ensure uniqueness
                        found_fonts.add(str(font_file.resolve()))

    return sorted(list(found_fonts))


if __name__ == '__main__':
    # A simple test script to demonstrate the module's functionality.
    # This will print the found font directories and the total count of font files.
    print("--- FontSnip Font Utility Test ---")

    print("\n[1] Discovering system font directories...")
    try:
        dirs = get_system_font_dirs()
        if not dirs:
            print("  - No standard font directories found or OS not supported.")
        else:
            print("  - Found the following existing directories:")
            for d in dirs:
                print(f"    - {d}")
    except Exception as e:
        print(f"  - An error occurred while getting font directories: {e}")

    print("\n[2] Searching for font files (.ttf, .otf)...")
    try:
        font_files = find_font_files()
        if not font_files:
            print("  - No font files found in the discovered directories.")
        else:
            print(f"  - Success! Found {len(font_files)} font files.")
            if font_files:
                print("\n  - Sample of found fonts (first 10):")
                for font_path in font_files[:10]:
                    print(f"    - {Path(font_path).name}")
                if len(font_files) > 10:
                    print("    - ... and many more.")
    except Exception as e:
        print(f"  - An error occurred while searching for font files: {e}")

    print("\n--- Test Complete ---")
```