import cv2
import numpy as np
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AnalysisResult:
    path:        str
    fruits:      list   # List[FruitRegion]
    results:     list   # List[ClassifiedFruit]
    annotated:   np.ndarray   # BGR frame with overlays drawn
    n_good:      int
    n_bad:       int


def analyze_image(path: str) -> Optional[AnalysisResult]:
    """
    Load a thermal image from disk, run detection + classification,
    and return annotated results — exactly like a live frame.

    Supports any image the TC001 might produce:
      - Raw 256x384 stacked frame (visual top, thermal bottom)
      - Already-rendered heatmap (colormap applied)
      - Snapshot saved by save_snapshot()

    Returns None if the image can't be loaded.
    """
    from detector   import detect_fruits
    from classifier import classify_all, draw_results

    if not os.path.exists(path):
        print(f"[ImageAnalyzer] File not found: {path}")
        return None

    frame = cv2.imread(path)
    if frame is None:
        print(f"[ImageAnalyzer] Could not read image: {path}")
        return None

    h, w = frame.shape[:2]

    # If raw stacked frame (256x384) — apply colormap to top half
    if w == 256 and h == 384:
        visual  = frame[0:192, :]
        heatmap = cv2.applyColorMap(visual, cv2.COLORMAP_JET)
    else:
        # Already a rendered heatmap — use as-is
        heatmap = frame.copy()

    fruits  = detect_fruits(heatmap)
    results = classify_all(fruits, heatmap)   # no thdata for static images
    annotated = draw_results(heatmap, results)

    # Burn "STATIC IMAGE" tag so it's clear this isn't live
    _stamp(annotated, os.path.basename(path))

    n_good = sum(1 for r in results if r.label == "Good")
    n_bad  = sum(1 for r in results if r.label == "Bad")

    print(f"[ImageAnalyzer] {os.path.basename(path)} → "
          f"{len(fruits)} fruit(s), {n_good} Good, {n_bad} Bad")

    return AnalysisResult(
        path      = path,
        fruits    = fruits,
        results   = results,
        annotated = annotated,
        n_good    = n_good,
        n_bad     = n_bad,
    )


def _stamp(frame: np.ndarray, filename: str):
    """Burn filename + STATIC ANALYSIS tag onto frame."""
    h, w  = frame.shape[:2]
    lines = ["[ STATIC ANALYSIS ]", filename]
    for i, line in enumerate(lines):
        cv2.putText(frame, line, (11, 19 + i * 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, line, (10, 18 + i * 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 180), 1, cv2.LINE_AA)