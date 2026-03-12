import cv2
import time

from camera import FRAMERATE
from temperature import SCALE, WIDTH, SPLIT

# ── Constants ─────────────────────────────────────────────────────────────────

DISPLAY_W = WIDTH * SCALE
DISPLAY_H = SPLIT * SCALE


class Recorder:
    """
    Handles video recording of the thermal display stream.
    Saves as AVI with XVID codec.

    Key bindings (handled in main):
      r — start recording
      t — stop recording
    """

    def __init__(self):
        self.recording = False
        self.writer    = None
        self.start     = None
        self.elapsed   = "00:00:00"
        self.filename  = None

    def start_recording(self):
        """Begin recording to a timestamped AVI file."""
        now            = time.strftime("%Y%m%d-%H%M%S")
        self.filename  = f"TC001_{now}.avi"
        self.writer    = cv2.VideoWriter(
            self.filename,
            cv2.VideoWriter_fourcc(*'XVID'),
            FRAMERATE,
            (DISPLAY_W, DISPLAY_H)
        )
        self.recording = True
        self.start     = time.time()
        print(f"[Recorder] Started: {self.filename}")

    def stop_recording(self):
        """Finalize and close the current recording."""
        if self.writer:
            self.writer.release()
            self.writer = None
        self.recording = False
        self.elapsed   = "00:00:00"
        print(f"[Recorder] Stopped: {self.filename}")

    def write(self, frame):
        """Write a frame and update elapsed time. Call once per loop iteration."""
        if self.recording and self.writer:
            self.elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start))
            self.writer.write(frame)

    def release(self):
        """Safe cleanup — stops recording if still active."""
        if self.recording:
            self.stop_recording()