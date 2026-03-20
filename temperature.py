import cv2
import numpy as np

from camera import WIDTH, SPLIT

SCALE = 3


class TempReader:
    def __init__(self):
        self.current_temp = 0.0
        self.mx           = 0
        self.my           = 0
        self.thdata       = None

    @staticmethod
    def decode(thdata, row: int, col: int) -> float:
        hi = int(thdata[row, col, 0])
        lo = int(thdata[row, col, 1]) * 256
        return round((hi + lo) / 64 - 273.15, 2)

    def get_stats(self, thdata) -> dict:
        lomax  = int(thdata[..., 1].max())
        posmax = thdata[..., 1].argmax()
        mcol, mrow = divmod(int(posmax), WIDTH)
        himax  = int(thdata[mcol, mrow, 0])
        maxtemp = round((himax + lomax * 256) / 64 - 273.15, 2)

        lomin  = int(thdata[..., 1].min())
        posmin = thdata[..., 1].argmin()
        lcol, lrow = divmod(int(posmin), WIDTH)
        himin  = int(thdata[lcol, lrow, 0])
        mintemp = round((himin + lomin * 256) / 64 - 273.15, 2)

        loavg  = thdata[..., 1].mean()
        hiavg  = thdata[..., 0].mean()
        avgtemp = round((hiavg + loavg * 256) / 64 - 273.15, 2)

        return {
            'max': maxtemp, 'max_pos': (mrow, mcol),
            'min': mintemp, 'min_pos': (lrow, lcol),
            'avg': avgtemp,
        }

    def update_thdata(self, thdata):
        self.thdata = thdata

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            self.mx, self.my = x, y
            if self.thdata is not None:
                real_x = min(x // SCALE, WIDTH - 1)
                real_y = min(y // SCALE, SPLIT - 1)
                if 0 <= real_y < self.thdata.shape[0] and 0 <= real_x < self.thdata.shape[1]:
                    self.current_temp = self.decode(self.thdata, real_y, real_x)