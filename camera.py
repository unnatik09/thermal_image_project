import subprocess
import numpy as np

WIDTH     = 256
HEIGHT    = 384
SPLIT     = HEIGHT // 2
FRAMERATE = 25


class ThermalCamera:
    def __init__(self, index: int = 1):
        self.index      = index
        self.frame_size = WIDTH * HEIGHT * 2  # yuyv422 = 2 bytes per pixel
        self.process    = self._open(index)
        print(f"[ThermalCamera] Connected at index {index}")

    def _open(self, index: int):
        return subprocess.Popen([
            'ffmpeg',
            '-f',          'avfoundation',
            '-video_size', f'{WIDTH}x{HEIGHT}',
            '-framerate',  str(FRAMERATE),
            '-i',          str(index),
            '-f',          'rawvideo',
            '-pix_fmt',    'yuyv422',
            '-',
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def read(self):
        raw = self.process.stdout.read(self.frame_size)
        if len(raw) != self.frame_size:
            print("[ThermalCamera] Stream ended or frame size mismatch.")
            return None, None

        frame  = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 2))
        imdata = frame[0:SPLIT, :]
        thdata = frame[SPLIT:HEIGHT, :]
        return imdata, thdata

    def release(self):
        self.process.terminate()
        print("[ThermalCamera] Released.")