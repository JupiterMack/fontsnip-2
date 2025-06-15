# src/ui/__init__.py

"""
Initializes the 'ui' sub-package for the FontSnip application.

This package contains all the user interface components, built primarily using PyQt6.
It is responsible for all visual interactions with the user, including:

1.  **Capture Mode**: A full-screen, semi-transparent overlay that allows the user
    to select a region of the screen with their mouse.
2.  **Results Display**: A small, non-intrusive window or notification that
    presents the top font matches to the user.
3.  **System Tray Icon**: A persistent icon in the system tray for managing the
    application's lifecycle (e.g., settings, quit).

By encapsulating all GUI logic here, we separate the presentation layer from the
core application logic (state management, processing, matching).
"""

# The following imports can be uncommented once the specific UI component
# files are created. This makes the main classes available directly under
# the `ui` namespace, e.g., `from ui import CaptureWindow`.

# from .capture_window import CaptureWindow
# from .results_window import ResultsWindow
# from .tray_icon import TrayIcon