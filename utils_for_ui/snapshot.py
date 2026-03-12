import cv2
import os
import time
import numpy as np


def save_snapshot(frame: np.ndarray, output_dir: str = ".") -> str:
    """
    Save current frame as PNG with timestamp burned into the image.

    Args:
        frame      : BGR numpy array (the rendered heatmap)
        output_dir : folder to save into

    Returns:
        full path of saved file
    """
    os.makedirs(output_dir, exist_ok=True)

    now      = time.strftime("%Y%m%d-%H%M%S")
    filename = f"TC001_snapshot_{now}.png"
    path     = os.path.join(output_dir, filename)

    snapshot = frame.copy()

    # Timestamp overlay — black shadow + white text
    label = f"TC001  {time.strftime('%Y-%m-%d  %H:%M:%S')}"
    cv2.putText(snapshot, label, (11, snapshot.shape[0] - 9),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(snapshot, label, (10, snapshot.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imwrite(path, snapshot)
    print(f"[Snapshot] Saved → {path}")
    return path