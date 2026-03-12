import subprocess
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

WIDTH = 256
HEIGHT = 384
SPLIT = HEIGHT // 2
FRAMERATE = 25


class ThermalCamera:
    """
    Handles ffmpeg subprocess connection to the TC001 thermal camera.
    Reads raw YUYV frames and splits them into visual + thermal data.
    """

    def __init__(self, index: int = 0):
        self.index = index
        self.frame_size = WIDTH * HEIGHT * 2  # yuyv422 = 2 bytes per pixel

        self.process = subprocess.Popen([
            'ffmpeg',
            '-f',          'avfoundation',
            '-video_size', f'{WIDTH}x{HEIGHT}',
            '-framerate',  str(FRAMERATE),
            '-i',          str(index),
            '-f',          'rawvideo',
            '-pix_fmt',    'yuyv422',   # no color conversion — preserves raw thermal bytes
            '-',
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        print(f"[ThermalCamera] Connected to camera index {index}")

    def read(self):
        """
        Read one frame from the camera.
        Returns (imdata, thdata) or (None, None) on failure.
        - imdata: top SPLIT rows — visual/YUV frame
        - thdata: bottom SPLIT rows — raw temperature bytes
        """
        raw = self.process.stdout.read(self.frame_size)

        if len(raw) != self.frame_size:
            print("[ThermalCamera] Stream ended or frame size mismatch.")
            return None, None

        frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 2))
        imdata = frame[0:SPLIT, :]
        thdata = frame[SPLIT:HEIGHT, :]

        return imdata, thdata

    def release(self):
        """Terminate the ffmpeg subprocess."""
        self.process.terminate()
        print("[ThermalCamera] Released.")