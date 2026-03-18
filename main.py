import sys
from PyQt5.QtWidgets import QApplication

from camera           import ThermalCamera
from temperature      import TempReader
from recorder         import Recorder
from utils_for_ui.settings import Settings
from ui.main_window   import MainWindow


def main():
    app      = QApplication(sys.argv)
    settings = Settings.load()
    settings.apply_to_detector()
    settings.apply_to_classifier()

    camera   = ThermalCamera(index=settings.camera_index)
    temp     = TempReader()
    recorder = Recorder()
    state    = {'detect': True, 'settings': settings}

    window   = MainWindow(camera, temp, recorder, state)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()