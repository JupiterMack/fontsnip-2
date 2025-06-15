# src/main.py

"""
The main entry point for the FontSnip application.

This script initializes the PyQt6 application, creates the main FontSnipApp
instance, and starts the application's event loop. This is the file that
should be executed to launch the program.
"""

import sys
import os

# This is a common practice to ensure that the application can be run
# directly from the command line, and that all relative imports within
# the 'src' package work correctly. It adds the project's root directory
# (the parent of 'src') to the Python path.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.app import FontSnipApp


def main():
    """
    Initializes and runs the FontSnip application.
    """
    # Create the PyQt Application instance.
    # sys.argv is passed to allow for command-line arguments, a standard practice.
    app = QApplication(sys.argv)

    # Set application metadata (optional but good practice for desktop apps)
    app.setOrganizationName("FontSnip")
    app.setApplicationName("FontSnip")

    # To prevent the application from closing when the last window is closed
    # (e.g., the capture or results window), as it should continue running in
    # the system tray.
    app.setQuitOnLastWindowClosed(False)

    # The main application logic is encapsulated in the FontSnipApp class.
    # This class will set up the tray icon, hotkey listener, etc.
    font_snip_app = FontSnipApp()

    # The run() method initializes the app's components (like loading the
    # font database and setting up the hotkey listener).
    try:
        font_snip_app.run()
    except Exception as e:
        # In a real application, you might show a critical error dialog here.
        print(f"Failed to initialize FontSnip: {e}", file=sys.stderr)
        sys.exit(1)

    # Start the Qt event loop. This call is blocking and will exit only when
    # the application is quit (e.g., via the tray icon's "Quit" action).
    # The return value of exec() is used for the exit code.
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
```