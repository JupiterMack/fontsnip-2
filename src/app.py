# src/app.py

"""
The main application class for FontSnip.

This module contains the FontSnipApp class, which orchestrates the entire
application workflow. It manages the state machine, sets up the system tray
icon, registers the global hotkey listener, and integrates all the different
components (UI, processing, matching).
"""

import sys
import os
import threading
import logging

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject, Qt

from pynput import keyboard
import pyperclip

# Local application imports
from config import config, FONT_DATABASE_PATH, ASSETS_DIR
from ui.capture_widget import CaptureWidget
from ui.result_display import ResultWindow
from processing.image_processor import ImageProcessor
from matching.font_matcher import FontMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FontSnipApp(QObject):
    """
    The core application class that manages state and orchestrates the workflow.
    Inherits from QObject to leverage Qt's signal/slot mechanism for thread safety.
    """
    # Signal to safely trigger capture from the non-GUI hotkey listener thread
    trigger_capture_signal = pyqtSignal()

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray

        self.capture_widget = None
        self.result_window = None
        self.hotkey_listener = None

        # State 1: Idle / Listening Mode
        logger.info("Initializing FontSnip application...")
        self.setup_tray_icon()

        try:
            logger.info("Loading core components...")
            self.image_processor = ImageProcessor()
            self.font_matcher = FontMatcher(FONT_DATABASE_PATH)
            logger.info("Components loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Font database not found at {FONT_DATABASE_PATH}")
            self.show_error_and_quit(
                "Font Database Not Found",
                f"The font feature database '{os.path.basename(FONT_DATABASE_PATH)}' was not found.\n\n"
                "Please run the database generation script first:\n"
                "python scripts/create_font_database.py"
            )
            return
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            self.show_error_and_quit(
                "Initialization Error",
                f"An unexpected error occurred during startup: {e}"
            )
            return

        # Connect the signal to the slot that starts the capture
        self.trigger_capture_signal.connect(self.start_capture)

        # Setup and start the global hotkey listener
        self.setup_hotkey_listener()
        logger.info(f"FontSnip is running. Press '{config.get('hotkey')}' to start.")

    def setup_tray_icon(self):
        """Creates and configures the system tray icon and its context menu."""
        icon_path = os.path.join(ASSETS_DIR, 'icon.png')
        if not os.path.exists(icon_path):
            logger.error(f"Application icon not found at {icon_path}")
            # The app can run without an icon, but it's a bad user experience.
            # We'll proceed but log the error.
            self.tray_icon = QSystemTrayIcon(self)
        else:
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)

        self.tray_icon.setToolTip("FontSnip - Identify fonts from your screen")

        menu = QMenu()
        
        # Settings Action (placeholder)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Quit Action
        quit_action = QAction("Quit FontSnip", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def setup_hotkey_listener(self):
        """Initializes and starts the global hotkey listener in a separate thread."""
        try:
            hotkey_str = config.get('hotkey')
            self.hotkey_listener = keyboard.GlobalHotKeys({
                hotkey_str: self.on_hotkey_activated
            })
            # The listener thread must be a daemon so it exits when the main app quits
            listener_thread = threading.Thread(target=self.hotkey_listener.start, daemon=True)
            listener_thread.start()
            logger.info(f"Global hotkey '{hotkey_str}' registered.")
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}", exc_info=True)
            self.show_error_and_quit(
                "Hotkey Error",
                f"Could not register the hotkey '{config.get('hotkey')}'.\n\n"
                "Another application might be using it. Please change the hotkey in the config and restart."
            )

    def on_hotkey_activated(self):
        """
        Callback executed by pynput when the hotkey is pressed.
        Emits a signal to interact with the main GUI thread safely.
        """
        logger.info("Hotkey activated. Emitting signal to start capture.")
        # Do not create GUI elements here. Emit a signal instead.
        self.trigger_capture_signal.emit()

    def start_capture(self):
        """
        State 2: Capture Mode. Creates and shows the full-screen capture overlay.
        This method is a slot connected to the trigger_capture_signal.
        """
        # Prevent multiple capture widgets if hotkey is spammed
        if self.capture_widget is not None and self.capture_widget.isVisible():
            return
            
        logger.info("Transitioning to Capture Mode.")
        self.capture_widget = CaptureWidget()
        self.capture_widget.region_selected.connect(self.process_capture)
        self.capture_widget.show()

    def process_capture(self, image_np, geometry):
        """
        States 3 & 4: Image Processing and Font Matching.
        This slot is triggered when the user selects a region in the CaptureWidget.
        """
        logger.info(f"Region captured at {geometry}. Starting processing pipeline.")
        
        # State 3: Image Processing
        try:
            recognized_data, preprocessed_image = self.image_processor.process_image(image_np)
            if not recognized_data:
                logger.warning("OCR did not find any high-confidence characters.")
                self.show_notification("No text found", "Could not identify any text in the selected area.")
                return
        except Exception as e:
            logger.error(f"Error during image processing: {e}", exc_info=True)
            self.show_notification("Processing Error", "An error occurred while processing the image.")
            return

        # State 4: Font Matching
        try:
            matches = self.font_matcher.find_best_matches(recognized_data, preprocessed_image)
            if not matches:
                logger.warning("Could not find any font matches.")
                self.show_notification("No Match Found", "Unable to find a matching font in the database.")
                return
        except Exception as e:
            logger.error(f"Error during font matching: {e}", exc_info=True)
            self.show_notification("Matching Error", "An error occurred while matching the font.")
            return

        # State 5: Display Results
        self.display_results(matches, geometry)

    def display_results(self, matches, geometry):
        """
        State 5: Displaying Results. Shows a small window with top matches.
        """
        logger.info(f"Top matches found: {[m[0] for m in matches]}")
        
        # Copy top match to clipboard
        top_match_name = matches[0][0]
        try:
            pyperclip.copy(top_match_name)
            logger.info(f"Copied '{top_match_name}' to clipboard.")
            self.tray_icon.showMessage(
                "Font Identified!",
                f"Top match: {top_match_name}\n(Copied to clipboard)",
                self.tray_icon.icon(),
                2000  # msec
            )
        except pyperclip.PyperclipException as e:
            logger.warning(f"Could not copy to clipboard: {e}")
            self.tray_icon.showMessage(
                "Font Identified!",
                f"Top match: {top_match_name}\n(Could not copy to clipboard)",
                QSystemTrayIcon.MessageIcon.Warning,
                2000
            )

        # Create and show the result window near the snipped area
        # Storing it as an instance attribute prevents it from being garbage collected
        self.result_window = ResultWindow(matches, geometry)
        self.result_window.show()

    def show_settings(self):
        """Placeholder for a future settings dialog."""
        logger.info("Settings action triggered.")
        QMessageBox.information(
            None,
            "Settings",
            f"Settings are configured in the `config.ini` file.\n\n"
            f"Current Hotkey: {config.get('hotkey')}"
        )

    def show_notification(self, title, message):
        """Utility to show a system tray notification."""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 3000)

    def show_error_and_quit(self, title, message):
        """Displays a critical error message box and then quits."""
        QMessageBox.critical(None, title, message)
        self.app.quit()

    def quit_app(self):
        """Cleans up and exits the application."""
        logger.info("Quit action triggered. Shutting down.")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.tray_icon.hide()
        self.app.quit()


def main():
    """Main entry point for the FontSnip application."""
    # Ensure high DPI scaling is handled correctly by Qt
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # The FontSnipApp instance will manage its own lifecycle via the system tray
    font_snip_app = FontSnipApp(app)
    
    # Start the Qt event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
```