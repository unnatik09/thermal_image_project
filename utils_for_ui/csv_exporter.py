import csv
import os
import time
from typing import List

from .logger import DetectionEntry

COLUMNS = [
    'timestamp', 'frame_number', 'fruit_id', 'label',
    'mad', 't_avg', 't_min', 't_max', 'diameter',
]


def export_to_csv(entries: List[DetectionEntry], path: str = None) -> str:
    """
    Write detection entries to a CSV file.

    Args:
        entries : list of DetectionEntry from DetectionLogger
        path    : output file path — auto-generated if not provided

    Returns:
        path of the written file
    """
    if not entries:
        print("[CSVExporter] Nothing to export.")
        return None

    if path is None:
        now  = time.strftime("%Y%m%d-%H%M%S")
        path = f"TC001_detections_{now}.csv"

    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None

    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                'timestamp':    e.timestamp,
                'frame_number': e.frame_number,
                'fruit_id':     e.fruit_id,
                'label':        e.label,
                'mad':          e.mad,
                't_avg':        e.t_avg,
                't_min':        e.t_min,
                't_max':        e.t_max,
                'diameter':     e.diameter,
            })

    print(f"[CSVExporter] Saved {len(entries)} entries → {path}")
    return path