# src/ui/capture_widget.py

"""
Defines the full-screen overlay widget for capturing a screen region.

This module contains the CaptureWidget class, which is responsible for creating a
borderless, semi-transparent window that covers the entire screen. It handles
mouse events to allow the user to draw a selection rectangle and emits a signal
containing the coordinates of the selected region upon completion.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QGuiApplication, QCursor, QKeyEvent, QMouseEvent, QPaintEvent


class CaptureWidget(QWidget):
    """
    A full-screen, semi-transparent widget for selecting a screen region.

    This widget overlays the entire screen, captures mouse input to define a
    rectangle, and emits a signal with the rectangle's geometry when the
    mouse button is released.

    Signals:
        region_selected (pyqtSignal): Emitted with a QRect object when a
                                      region has been selected.
    """
    # Signal to be emitted when a region is selected, passing the QRect
    region_selected = pyqtSignal(QRect)

    def __init__(self, parent: QWidget | None = None):
        """
        Initializes the CaptureWidget.
        """
        super().__init__(parent)

        # Get the geometry of the primary screen
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        # Set window flags for a borderless, stay-on-top overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Prevents showing in the taskbar
        )
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set the cursor to a crosshair
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        # State variables for selection
        self._start_pos: QPoint | None = None
        self._end_pos: QPoint | None = None
        self._is_selecting: bool = False

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handles key press events. Closes the widget if Escape is pressed.

        Args:
            event: The QKeyEvent object.
        """
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handles the start of a mouse drag operation.

        Args:
            event: The QMouseEvent object.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_selecting = True
            self._start_pos = event.position().toPoint()
            self._end_pos = self._start_pos
            self.update()  # Trigger a repaint
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handles mouse movement during a drag operation to update the selection
        rectangle.

        Args:
            event: The QMouseEvent object.
        """
        if self._is_selecting:
            self._end_pos = event.position().toPoint()
            self.update()  # Trigger a repaint to show the updated rectangle
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Handles the end of a mouse drag operation, finalizing the selection.

        Args:
            event: The QMouseEvent object.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            selection_rect = QRect(self._start_pos, self._end_pos).normalized()

            # Ensure the selection has a valid size (e.g., not just a click)
            if selection_rect.width() > 5 and selection_rect.height() > 5:
                self.region_selected.emit(selection_rect)

            self.close()  # Close the widget after selection
            event.accept()

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Paints the widget, including the semi-transparent overlay and the
        selection rectangle.

        Args:
            event: The QPaintEvent object.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the semi-transparent overlay across the entire screen
        overlay_color = QColor(20, 20, 20, 120)
        painter.fillRect(self.rect(), overlay_color)

        if self._is_selecting and self._start_pos and self._end_pos:
            selection_rect = QRect(self._start_pos, self._end_pos).normalized()

            # Clear the area inside the selection rectangle
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Draw a border around the selection rectangle
            pen = QPen(QColor(50, 150, 255), 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

    def start_capture(self):
        """
        Shows the widget to begin the capture process.
        """
        self.show()
        self.activateWindow()
        self.raise_()


if __name__ == '__main__':
    import sys

    def on_region_selected(rect: QRect):
        """A simple slot to test the signal."""
        print(f"Region selected: x={rect.x()}, y={rect.y()}, w={rect.width()}, h={rect.height()}")
        # In the real app, this would trigger the mss capture.
        # We need to quit the app here for the test to exit.
        QApplication.instance().quit()

    app = QApplication(sys.argv)
    capture_widget = CaptureWidget()
    capture_widget.region_selected.connect(on_region_selected)
    capture_widget.start_capture()
    sys.exit(app.exec())
```