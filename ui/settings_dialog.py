from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QSpinBox, QPushButton, QFormLayout, QFrame
)
from PyQt5.QtCore import Qt


DIALOG_STYLE = """
    QDialog {
        background-color: #0d0d0d;
        color: #cccccc;
    }
    QLabel {
        color: #aaaaaa;
        font-family: 'Courier New';
        font-size: 11px;
    }
    QSpinBox, QDoubleSpinBox {
        background-color: #1a1a1a;
        color: #00ff88;
        border: 1px solid #333;
        border-radius: 3px;
        padding: 3px;
        font-family: 'Courier New';
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: #333;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #00ff88;
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }
    QSlider::sub-page:horizontal {
        background: #00aa55;
        border-radius: 2px;
    }
    QPushButton {
        background-color: #1a1a1a;
        color: #00ff88;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 6px 16px;
        font-family: 'Courier New';
        font-size: 11px;
    }
    QPushButton:hover { background-color: #222; }
"""


class SettingsDialog(QDialog):
    """
    Modal settings panel — edits entropy threshold and fruit area limits live.
    Changes are applied immediately; Cancel reverts to previous values.
    """

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._prev    = {
            'entropy_threshold': settings.entropy_threshold,
            'min_fruit_area':    settings.min_fruit_area,
            'max_fruit_area':    settings.max_fruit_area,
        }
        self.setWindowTitle("Settings")
        self.setStyleSheet(DIALOG_STYLE)
        self.setFixedSize(360, 300)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⚙  SETTINGS")
        title.setStyleSheet("color: #00ff88; font-size: 14px; font-weight: bold; "
                            "letter-spacing: 2px; font-family: 'Courier New';")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # Entropy threshold
        self.entropy_slider = QSlider(Qt.Horizontal)
        self.entropy_slider.setRange(10, 70)   # 1.0 – 7.0 bits × 10
        self.entropy_slider.setValue(int(self.settings.entropy_threshold * 10))
        self.entropy_val = QLabel(f"{self.settings.entropy_threshold:.1f} bits")
        self.entropy_val.setStyleSheet("color: #00ff88; font-family: 'Courier New';")
        self.entropy_slider.valueChanged.connect(self._on_entropy)
        row = QHBoxLayout()
        row.addWidget(self.entropy_slider)
        row.addWidget(self.entropy_val)
        form.addRow("Entropy Threshold", row)

        # Min fruit area
        self.spin_min = QSpinBox()
        self.spin_min.setRange(500, 50000)
        self.spin_min.setSingleStep(500)
        self.spin_min.setValue(self.settings.min_fruit_area)
        self.spin_min.valueChanged.connect(self._on_min_area)
        form.addRow("Min Fruit Area (px²)", self.spin_min)

        # Max fruit area
        self.spin_max = QSpinBox()
        self.spin_max.setRange(10000, 500000)
        self.spin_max.setSingleStep(5000)
        self.spin_max.setValue(self.settings.max_fruit_area)
        self.spin_max.valueChanged.connect(self._on_max_area)
        form.addRow("Max Fruit Area (px²)", self.spin_max)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_save   = QPushButton("SAVE")
        btn_cancel = QPushButton("CANCEL")
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _on_entropy(self, val):
        v = val / 10
        self.settings.entropy_threshold = v
        self.entropy_val.setText(f"{v:.1f} bits")
        self._apply()

    def _on_min_area(self, val):
        self.settings.min_fruit_area = val
        self._apply()

    def _on_max_area(self, val):
        self.settings.max_fruit_area = val
        self._apply()

    def _apply(self):
        self.settings.apply_to_detector()
        self.settings.apply_to_classifier()

    def _save(self):
        self.settings.save()
        self.accept()

    def _cancel(self):
        for k, v in self._prev.items():
            setattr(self.settings, k, v)
        self._apply()
        self.reject()