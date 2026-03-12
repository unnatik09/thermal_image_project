import numpy as np
import cv2

from camera import WIDTH, SPLIT

# ── Constants ─────────────────────────────────────────────────────────────────

SCALE = 3


class TempReader:
    """
    Handles temperature decoding from raw thermal byte data,
    and tracks mouse position for live temp readout.
    """

    def __init__(self):
        self.current_temp = 0.0
        self.mx           = 0
        self.my           = 0
        self.thdata       = None

    @staticmethod
    def decode(thdata, row: int, col: int) -> float:
        """
        Decode temperature from raw YUYV thermal bytes.
        Formula from TC001 datasheet / LeoDJ reverse engineering:
          raw = hi + lo * 256
          temp = (raw / 64) - 273.15
        """
        hi = int(thdata[row, col, 0])
        lo = int(thdata[row, col, 1]) * 256
        return round((hi + lo) / 64 - 273.15, 2)

    @staticmethod
    def get_stats(thdata) -> dict:
        """
        Compute min, max and average temperature across the full thermal frame.
        Returns dict with keys: min, max, avg and their pixel positions.
        """
        # Max
        lomax   = int(thdata[..., 1].max())
        posmax  = thdata[..., 1].argmax()
        mcol, mrow = divmod(posmax, WIDTH)
        himax   = int(thdata[mcol, mrow, 0])
        maxtemp = round((himax + lomax * 256) / 64 - 273.15, 2)

        # Min
        lomin   = int(thdata[..., 1].min())
        posmin  = thdata[..., 1].argmin()
        lcol, lrow = divmod(posmin, WIDTH)
        himin   = int(thdata[lcol, lrow, 0])
        mintemp = round((himin + lomin * 256) / 64 - 273.15, 2)

        # Avg
        loavg   = thdata[..., 1].mean()
        hiavg   = thdata[..., 0].mean()
        avgtemp = round((hiavg + loavg * 256) / 64 - 273.15, 2)

        return {
            'max': maxtemp, 'max_pos': (mrow, mcol),
            'min': mintemp, 'min_pos': (lrow, lcol),
            'avg': avgtemp,
        }

    def update_thdata(self, thdata):
        """Update the current thermal frame for mouse callback use."""
        self.thdata = thdata

    def on_mouse(self, event, x, y, flags, param):
        """OpenCV mouse callback — updates current temp at cursor position."""
        if event == cv2.EVENT_MOUSEMOVE:
            self.mx, self.my = x, y
            if self.thdata is not None:
                real_x = min(x // SCALE, WIDTH - 1)
                real_y = min(y // SCALE, SPLIT - 1)
                if 0 <= real_y < self.thdata.shape[0] and 0 <= real_x < self.thdata.shape[1]:
                    self.current_temp = self.decode(self.thdata, real_y, real_x)