import cv2
import os
import time
import numpy as np


def save_snapshot(frame: np.ndarray, output_dir: str = "snapshots") -> str:
    """
    Save current frame as PNG with timestamp overlay.
    Creates output_dir if it doesn't exist.
    Returns full path of saved file.
    """
    os.makedirs(output_dir, exist_ok=True)

    now      = time.strftime("%Y%m%d-%H%M%S")
    path     = os.path.join(output_dir, f"TC001_{now}.png")
    snapshot = frame.copy()

    h, w     = snapshot.shape[:2]
    label    = f"TC001  {time.strftime('%Y-%m-%d  %H:%M:%S')}"

    # Black shadow + white text bottom-left
    cv2.putText(snapshot, label, (11, h - 9),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(snapshot, label, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # Small resolution tag top-right
    res_tag = f"{w}x{h}"
    (tw, _), _ = cv2.getTextSize(res_tag, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
    cv2.putText(snapshot, res_tag, (w - tw - 9, 19),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(snapshot, res_tag, (w - tw - 10, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)

    cv2.imwrite(path, snapshot)
    print(f"[Snapshot] Saved → {path}")
    return path