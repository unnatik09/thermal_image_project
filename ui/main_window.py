import cv2
import numpy as np

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from PyQt5.QtCore    import QTimer, Qt, pyqtSlot
from PyQt5.QtGui     import QKeySequence

from ui.feed_widget     import FeedWidget
from ui.control_panel   import ControlPanel
from ui.settings_dialog import SettingsDialog


WINDOW_STYLE = """
    QMainWindow {
        background-color: #080808;
    }
    QWidget#central {
        background-color: #080808;
    }
"""


class MainWindow(QMainWindow):
    """
    Root window — 800x480 for Pi touchscreen.
    Left: live thermal feed. Right: control panel.
    """

    def __init__(self, camera, temp_reader, recorder, app_state):
        super().__init__()
        self.camera      = camera
        self.temp_reader = temp_reader
        self.recorder    = recorder
        self.state       = app_state    # dict: detect, settings
        self.heatmap     = None

        self.setWindowTitle("TC001 Thermal Scanner")
        self.setFixedSize(800, 480)
        self.setStyleSheet(WINDOW_STYLE)
        self._build_ui()
        self._start_timer()

    def _build_ui(self):
        central = QWidget(objectName="central")
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.feed    = FeedWidget()
        self.panel   = ControlPanel()
        layout.addWidget(self.feed,  stretch=1)
        layout.addWidget(self.panel, stretch=0)

        # Connect panel signals
        self.panel.sig_record.connect(self._on_record)
        self.panel.sig_stop.connect(self._on_stop)
        self.panel.sig_detect.connect(self._on_detect)
        self.panel.sig_snap.connect(self._on_snap)
        self.panel.sig_analyze.connect(self._on_analyze)
        self.panel.sig_settings.connect(self._on_settings)
        self.panel.sig_quit.connect(self.close)

    def _start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)   # ~25 fps

    # ── Frame loop ────────────────────────────────────────────────────────────

    def _tick(self):
        from detector   import detect_fruits
        from classifier import classify_all, draw_results

        imdata, thdata = self.camera.read()
        if imdata is None:
            self.timer.stop()
            return

        self.temp_reader.update_thdata(thdata)

        # Build heatmap
        bgr     = cv2.cvtColor(imdata, cv2.COLOR_YUV2BGR_YUYV)
        bgr     = cv2.resize(bgr, (self.feed.width(), self.feed.height()),
                              interpolation=cv2.INTER_CUBIC)
        heatmap = cv2.applyColorMap(bgr, cv2.COLORMAP_JET)

        # Detection
        n_good = n_bad = 0
        avg_entropy = 0.0

        if self.state['detect']:
            fruits  = detect_fruits(heatmap)
            results = classify_all(fruits, heatmap, thdata)
            heatmap = draw_results(heatmap, results)
            n_good  = sum(1 for r in results if r.label == "Good")
            n_bad   = sum(1 for r in results if r.label == "Bad")
            if results:
                avg_entropy = sum(r.entropy for r in results) / len(results)

        # Crosshair
        from camera import SPLIT, WIDTH
        from temperature import SCALE
        cx = heatmap.shape[1] // 2
        cy = heatmap.shape[0] // 2
        cv2.line(heatmap, (cx, cy+20), (cx, cy-20), (255,255,255), 2)
        cv2.line(heatmap, (cx+20, cy), (cx-20, cy), (255,255,255), 2)

        center_temp = self.temp_reader.decode(thdata, SPLIT//2, WIDTH//2)

        self.heatmap = heatmap
        self.feed.update_frame(heatmap)

        if self.recorder.recording:
            self.recorder.write(heatmap)

        # Update panel stats
        self.panel.update_temps(center_temp, self.temp_reader.current_temp)
        self.panel.update_detection(n_good + n_bad, n_good, n_bad, avg_entropy)
        self.panel.update_recording(self.recorder.recording, self.recorder.elapsed)

    # ── Button handlers ───────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_record(self):
        if not self.recorder.recording:
            self.recorder.start_recording()

    @pyqtSlot()
    def _on_stop(self):
        if self.recorder.recording:
            self.recorder.stop_recording()

    @pyqtSlot()
    def _on_detect(self):
        self.state['detect'] = not self.state['detect']
        self.panel.set_detect_state(self.state['detect'])

    @pyqtSlot()
    def _on_snap(self):
        if self.heatmap is not None:
            from utils_for_ui.snapshot import save_snapshot
            save_snapshot(self.heatmap,
                          output_dir=self.state['settings'].snapshot_dir)

    @pyqtSlot()
    def _on_analyze(self):
        from ui.main_window import open_image_analyzer
        open_image_analyzer(self)

    @pyqtSlot()
    def _on_settings(self):
        dlg = SettingsDialog(self.state['settings'], parent=self)
        dlg.exec_()

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_R:   self._on_record()
        elif key == Qt.Key_T: self._on_stop()
        elif key == Qt.Key_D: self._on_detect()
        elif key == Qt.Key_P: self._on_snap()
        elif key == Qt.Key_Q: self.close()

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.timer.stop()
        self.recorder.release()
        self.camera.release()
        event.accept()


# ── Image Analysis Dialog ─────────────────────────────────────────────────────

def open_image_analyzer(parent):
    """
    Open file picker → run analysis → show result in a popup window.
    Can be called from anywhere via: open_image_analyzer(self)
    """
    from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QLabel, QScrollArea
    from PyQt5.QtGui     import QImage, QPixmap
    from PyQt5.QtCore    import Qt
    from utils_for_ui.image_analyzer import analyze_image

    path, _ = QFileDialog.getOpenFileName(
        parent, "Open Thermal Image", "",
        "Images (*.png *.jpg *.jpeg *.bmp)"
    )
    if not path:
        return

    result = analyze_image(path)
    if result is None:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "Error", f"Could not analyze:\n{path}")
        return

    # Show annotated frame in a dialog
    dlg = QDialog(parent)
    dlg.setWindowTitle(f"Analysis — {result.n_good} Good  {result.n_bad} Bad")
    dlg.setStyleSheet("background-color: #0d0d0d;")
    dlg.resize(820, 560)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(8)

    # Stats bar
    stats = QLabel(
        f"  Fruits detected: {len(result.fruits)}    "
        f"✓ Good: {result.n_good}    "
        f"✗ Bad: {result.n_bad}  "
    )
    stats.setStyleSheet(
        "color: #00ff88; background: #111; font-family: 'Courier New'; "
        "font-size: 12px; padding: 6px; border: 1px solid #222;"
    )
    layout.addWidget(stats)

    # Image
    frame = result.annotated
    rgb   = __import__('cv2').cvtColor(frame, __import__('cv2').COLOR_BGR2RGB)
    h, w, c = rgb.shape
    qimg  = QImage(rgb.data, w, h, w * c, QImage.Format_RGB888)
    img_label = QLabel()
    img_label.setPixmap(QPixmap.fromImage(qimg).scaled(
        800, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation
    ))
    img_label.setAlignment(Qt.AlignCenter)
    img_label.setStyleSheet("background: #000;")
    layout.addWidget(img_label)

    dlg.exec_()