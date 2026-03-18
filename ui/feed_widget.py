from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QImage, QPixmap
import numpy as np
import cv2


class FeedWidget(QLabel):
    """
    Displays the live thermal camera feed.
    Receives BGR numpy frames and renders them as a QPixmap.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #0a0a0a;")
        self.setMinimumSize(512, 384)

    def update_frame(self, frame: np.ndarray):
        """Convert BGR numpy array to QPixmap and display."""
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = rgb.shape
        qimg    = QImage(rgb.data, w, h, w * c, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))