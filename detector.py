import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List


# ── Constants ─────────────────────────────────────────────────────────────────

MIN_FRUIT_AREA = 3000    # px² — ignore tiny blobs
MAX_FRUIT_AREA = 200000  # px² — ignore full-frame noise


# ── Data Class ────────────────────────────────────────────────────────────────

@dataclass
class FruitRegion:
    contour: np.ndarray
    bbox:    Tuple[int, int, int, int]  # x, y, w, h
    center:  Tuple[int, int]
    area:    float
    mask:    np.ndarray                 # binary mask, same size as heatmap


# ── Segmentation ──────────────────────────────────────────────────────────────

def segment_fruits(heatmap: np.ndarray) -> np.ndarray:
    """
    Isolate cool fruit regions from warm background in a JET colormap heatmap.

    In COLORMAP_JET:
      cool regions → blue dominant (high B, low R)
      warm background → red dominant (high R, low B)

    Returns binary mask of fruit regions.
    """
    b, g, r = cv2.split(heatmap)

    # Cool map: pixels where blue significantly exceeds red
    cool_map = np.clip(b.astype(np.int16) - r.astype(np.int16), 0, 255).astype(np.uint8)
    _, mask  = cv2.threshold(cool_map, 40, 255, cv2.THRESH_BINARY)

    # Morphological cleanup — close gaps, remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)

    return mask


def detect_fruits(heatmap: np.ndarray) -> List[FruitRegion]:
    """
    Detect fruit blobs in a JET heatmap frame.

    Returns a list of FruitRegion — one per detected blob.
    Each FruitRegion carries only geometry + mask, no classification.
    """
    mask       = segment_fruits(heatmap)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    fruits = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if not (MIN_FRUIT_AREA <= area <= MAX_FRUIT_AREA):
            continue

        x, y, w, h  = cv2.boundingRect(cnt)
        region_mask = np.zeros(heatmap.shape[:2], dtype=np.uint8)
        cv2.drawContours(region_mask, [cnt], -1, 255, -1)

        fruits.append(FruitRegion(
            contour = cnt,
            bbox   = (x, y, w, h),
            center  = (x + w // 2, y + h // 2),
            area    = area,
            mask    = region_mask,
        ))

    return fruits