import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class DetectionEntry:
    timestamp:    str
    frame_number: int
    fruit_id:     int
    label:        str    # "Good" | "Bad"
    mad:          float
    t_avg:        float
    t_min:        float
    t_max:        float
    diameter:     float  # 2 * sqrt(pixel_area / pi)


class DetectionLogger:
    """
    Accumulates DetectionEntry records during a session.
    Stays in memory — hand off to csv_exporter to persist.
    """

    def __init__(self):
        self.entries: List[DetectionEntry] = []

    def log(self, timestamp: str, frame_number: int, fruit_id: int,
            label: str, mad: float, t_avg: float, t_min: float,
            t_max: float, pixel_area: float) -> DetectionEntry:
        """Build and store a DetectionEntry. Returns the entry."""
        diameter = round(2 * math.sqrt(pixel_area / math.pi), 2)

        entry = DetectionEntry(
            timestamp    = timestamp,
            frame_number = frame_number,
            fruit_id     = fruit_id,
            label        = label,
            mad          = round(mad,   3),
            t_avg        = round(t_avg, 2),
            t_min        = round(t_min, 2),
            t_max        = round(t_max, 2),
            diameter     = diameter,
        )
        self.entries.append(entry)
        return entry

    def clear(self):
        self.entries.clear()

    def __len__(self):
        return len(self.entries)