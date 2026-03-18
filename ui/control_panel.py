from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSizePolicy
)
from PyQt5.QtCore  import Qt, pyqtSignal
from PyQt5.QtGui   import QFont


BTN_BASE = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
    }}
    QPushButton:hover {{ background-color: {hover}; }}
    QPushButton:pressed {{ background-color: {border}; }}
    QPushButton:disabled {{ background-color: #1a1a1a; color: #444; border-color: #333; }}
"""

def _btn_style(bg, fg, border, hover):
    return BTN_BASE.format(bg=bg, fg=fg, border=border, hover=hover)

STYLE_REC        = _btn_style('#8b0000', '#ff6666', '#cc0000', '#a00000')
STYLE_STOP       = _btn_style('#1a1a1a', '#ff6666', '#cc0000', '#2a1010')
STYLE_DETECT     = _btn_style('#003300', '#66ff88', '#00aa44', '#004400')
STYLE_DETECT_OFF = _btn_style('#1a1a1a', '#446644', '#2a4a2a', '#222')
STYLE_SNAP       = _btn_style('#1a1a2e', '#88aaff', '#3355aa', '#1e2a4a')
STYLE_ANALYZE    = _btn_style('#1e1a2e', '#bb88ff', '#6633aa', '#2a1e4a')
STYLE_SETTINGS   = _btn_style('#1a1a1a', '#aaaaaa', '#444444', '#2a2a2a')
STYLE_QUIT       = _btn_style('#0a0a0a', '#666666', '#333333', '#1a1a1a')

STAT_LABEL = "QLabel { color: #00ff88; font-size: 11px; font-family: 'Courier New'; padding: 2px 0; }"
STAT_VALUE = "QLabel { color: #ffffff; font-size: 12px; font-family: 'Courier New'; font-weight: bold; padding: 2px 0; }"
DIVIDER    = "QFrame { color: #222222; }"


class ControlPanel(QWidget):
    sig_record   = pyqtSignal()
    sig_stop     = pyqtSignal()
    sig_detect   = pyqtSignal()
    sig_snap     = pyqtSignal()
    sig_analyze  = pyqtSignal()
    sig_settings = pyqtSignal()
    sig_quit     = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self.setStyleSheet("background-color: #0d0d0d;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(6)

        title = QLabel("TC001")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00ff88; font-size: 18px; font-weight: bold; "
                            "font-family: 'Courier New'; letter-spacing: 3px; padding: 4px;")
        layout.addWidget(title)

        sub = QLabel("THERMAL SCANNER")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446644; font-size: 8px; letter-spacing: 2px; "
                          "font-family: 'Courier New'; padding-bottom: 6px;")
        layout.addWidget(sub)

        layout.addWidget(self._divider())
        layout.addWidget(self._section("TEMPERATURE"))
        self.lbl_center = self._stat_row(layout, "CENTER")
        self.lbl_cursor = self._stat_row(layout, "CURSOR")

        layout.addWidget(self._divider())
        layout.addWidget(self._section("DETECTION"))
        self.lbl_fruits  = self._stat_row(layout, "FRUITS")
        self.lbl_good    = self._stat_row(layout, "GOOD")
        self.lbl_bad     = self._stat_row(layout, "BAD")
        self.lbl_entropy = self._stat_row(layout, "ENTROPY")

        layout.addWidget(self._divider())
        layout.addWidget(self._section("RECORDING"))
        self.lbl_rec_status = self._stat_row(layout, "STATUS")
        self.lbl_rec_time   = self._stat_row(layout, "TIME")

        layout.addStretch()
        layout.addWidget(self._divider())

        self.btn_rec     = self._btn("● REC",        STYLE_REC,      self.sig_record)
        self.btn_stop    = self._btn("■ STOP",        STYLE_STOP,     self.sig_stop)
        self.btn_det     = self._btn("◈ DETECT",      STYLE_DETECT,   self.sig_detect)
        self.btn_snap    = self._btn("⊡ SNAPSHOT",    STYLE_SNAP,     self.sig_snap)
        self.btn_analyze = self._btn("⊞ ANALYZE IMG", STYLE_ANALYZE,  self.sig_analyze)
        self.btn_set     = self._btn("⚙ SETTINGS",    STYLE_SETTINGS, self.sig_settings)
        self.btn_quit    = self._btn("✕ QUIT",        STYLE_QUIT,     self.sig_quit)

        for btn in [self.btn_rec, self.btn_stop, self.btn_det,
                    self.btn_snap, self.btn_analyze, self.btn_set, self.btn_quit]:
            layout.addWidget(btn)

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(DIVIDER)
        return line

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #334433; font-size: 8px; letter-spacing: 2px; "
                          "font-family: 'Courier New'; padding-top: 2px;")
        return lbl

    def _stat_row(self, layout, label_text):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(STAT_LABEL)
        val = QLabel("--")
        val.setStyleSheet(STAT_VALUE)
        val.setAlignment(Qt.AlignRight)
        row.addWidget(lbl)
        row.addWidget(val)
        layout.addLayout(row)
        return val

    def _btn(self, text, style, signal):
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.setFixedHeight(30)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.clicked.connect(signal.emit)
        return btn

    def update_temps(self, center: float, cursor: float):
        self.lbl_center.setText(f"{center:.1f} C")
        self.lbl_cursor.setText(f"{cursor:.1f} C")

    def update_detection(self, n_fruits, n_good, n_bad, entropy):
        self.lbl_fruits.setText(str(n_fruits))
        self.lbl_good.setText(str(n_good))
        self.lbl_bad.setText(f"<font color='#ff4444'>{n_bad}</font>" if n_bad > 0 else "0")
        self.lbl_bad.setTextFormat(Qt.RichText)
        self.lbl_entropy.setText(f"{entropy:.2f} b")

    def update_recording(self, recording: bool, elapsed: str):
        if recording:
            self.lbl_rec_status.setText("<font color='#ff4444'>● REC</font>")
            self.lbl_rec_status.setTextFormat(Qt.RichText)
            self.lbl_rec_time.setText(elapsed)
        else:
            self.lbl_rec_status.setText("IDLE")
            self.lbl_rec_time.setText("--")

    def set_detect_state(self, active: bool):
        self.btn_det.setStyleSheet(STYLE_DETECT if active else STYLE_DETECT_OFF)
        self.btn_det.setText("◈ DETECT ON" if active else "◈ DETECT OFF")