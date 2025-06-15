# src/ui/result_display.py

"""
Defines the result display window for FontSnip.

This module contains the ResultWindow class, a small, non-intrusive widget
that appears near the captured screen area to display the top font matches.
It automatically copies the best match to the clipboard.
"""

import logging
from typing import List

import pyperclip
from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QFocusEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

# Configure logging
logger = logging.getLogger(__name__)

# Constants
WINDOW_TIMEOUT_MS = 5000  # Window closes after 5 seconds
WINDOW_PADDING = 15       # Padding inside the window
POSITION_OFFSET = 10      # Offset from the snip rectangle


class ResultWindow(QWidget):
    """
    A small, temporary window to display font matching results.

    This window is frameless, stays on top, and positions itself near the
    original screen capture area. It displays the top 3 font matches and
    copies the best match to the clipboard. It closes automatically after a
    timeout, on click, or when it loses focus.
    """

    def __init__(self, matches: List[str], snip_rect: QRect, parent: QWidget = None):
        """
        Initializes the ResultWindow.

        Args:
            matches (List[str]): A list of top font name matches.
            snip_rect (QRect): The geometry of the screen capture, used for positioning.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        if not matches:
            logger.warning("ResultWindow initialized with no matches. Window will not show.")
            # We can't do much without matches, so we'll just be an invisible widget
            # that gets garbage collected.
            return

        self.matches = matches
        self.snip_rect = snip_rect

        self._setup_window_properties()
        self._init_ui()
        self._position_window()
        self._copy_to_clipboard()

        # Automatically close the window after a set duration
        QTimer.singleShot(WINDOW_TIMEOUT_MS, self.close)

    def _setup_window_properties(self):
        """Sets the window flags and styling."""
        self.setWindowFlags(
            Qt.WindowType.Tool |          # Don't show in taskbar
            Qt.WindowType.FramelessWindowHint |  # No border or title bar
            Qt.WindowType.WindowStaysOnTopHint   # Always on top
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Important for memory management
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.9);
                color: #FFFFFF;
                border-radius: 8px;
                font-family: sans-serif;
            }
            QLabel#title {
                font-size: 13px;
                font-weight: bold;
                color: #AAAAAA;
                padding-bottom: 5px;
                border-bottom: 1px solid #444444;
            }
            QLabel#top_match {
                font-size: 16px;
                font-weight: bold;
                padding-top: 5px;
            }
            QLabel#other_match {
                font-size: 14px;
                color: #DDDDDD;
            }
        """)

    def _init_ui(self):
        """Creates and arranges the widgets within the window."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            WINDOW_PADDING, WINDOW_PADDING // 2, WINDOW_PADDING, WINDOW_PADDING
        )
        layout.setSpacing(4)

        title_label = QLabel("Top Matches")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Top match
        top_match_text = f"{self.matches[0]} (copied)"
        top_match_label = QLabel(top_match_text)
        top_match_label.setObjectName("top_match")
        top_match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_match_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(top_match_label)

        # Other matches
        for match_name in self.matches[1:3]:  # Display up to 2 other matches
            other_match_label = QLabel(match_name)
            other_match_label.setObjectName("other_match")
            other_match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            other_match_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(other_match_label)

        self.setLayout(layout)
        self.adjustSize() # Adjust size to content

    def _position_window(self):
        """
        Calculates the optimal position for the window near the snip rectangle,
        ensuring it stays within the screen bounds.
        """
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_size = self.sizeHint()

        # Default position: below the snip, centered horizontally
        pos_x = self.snip_rect.x() + (self.snip_rect.width() - window_size.width()) // 2
        pos_y = self.snip_rect.y() + self.snip_rect.height() + POSITION_OFFSET

        # Adjust if it goes off the bottom of the screen
        if pos_y + window_size.height() > screen_geometry.y() + screen_geometry.height():
            # Place it above the snip instead
            pos_y = self.snip_rect.y() - window_size.height() - POSITION_OFFSET

        # Adjust if it goes off the right side of the screen
        if pos_x + window_size.width() > screen_geometry.x() + screen_geometry.width():
            pos_x = screen_geometry.x() + screen_geometry.width() - window_size.width()

        # Ensure it doesn't go off the left or top
        pos_x = max(screen_geometry.x(), pos_x)
        pos_y = max(screen_geometry.y(), pos_y)

        self.move(int(pos_x), int(pos_y))

    def _copy_to_clipboard(self):
        """Copies the top font match to the system clipboard."""
        if self.matches:
            top_match = self.matches[0]
            try:
                pyperclip.copy(top_match)
                logger.info(f"Copied '{top_match}' to clipboard.")
            except pyperclip.PyperclipException as e:
                logger.error(f"Failed to copy to clipboard: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        """Closes the window when clicked."""
        logger.debug("Result window clicked, closing.")
        self.close()
        event.accept()

    def focusOutEvent(self, event: QFocusEvent):
        """Closes the window when it loses focus."""
        logger.debug("Result window lost focus, closing.")
        self.close()
        event.accept()
```