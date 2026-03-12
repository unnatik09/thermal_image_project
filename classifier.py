import numpy as np
import cv2
from dataclasses import dataclass
from typing import List, Tuple

from detector import FruitRegion


# ── Constants ─────────────────────────────────────────────────────────────────

# Sum of |T - T_avg| per pixel, normalised by region area.
# If mean absolute deviation exceeds this threshold → BAD fruit.
MAD_THRESHOLD = 2.0   # °C — tune this based on your fruit/camera


# ── Data Class ────────────────────────────────────────────────────────────────

@dataclass
class ClassifiedFruit:
    region:    FruitRegion
    temps:     np.ndarray   # 1D array of per-pixel temperatures (°C)
    t_avg:     float        # mean temperature of the region
    mad:       float        # mean |T - T_avg| across all pixels
    label:     str          # "Good" | "Bad"


# ── Temperature Extraction ────────────────────────────────────────────────────

def extract_temps_from_thdata(mask: np.ndarray, thdata: np.ndarray,
                               heatmap_shape: Tuple[int, int]) -> np.ndarray:
    """
    Extract per-pixel temperatures (°C) for a region using raw thdata bytes.

    thdata is SPLIT x WIDTH x 2 — needs rescaling to match heatmap size.
    """
    th_mask = cv2.resize(mask,
                         (thdata.shape[1], thdata.shape[0]),
                         interpolation=cv2.INTER_NEAREST)
    ys, xs = np.where(th_mask > 0)
    if len(ys) == 0:
        return np.array([])

    hi   = thdata[ys, xs, 0].astype(np.float32)
    lo   = thdata[ys, xs, 1].astype(np.float32) * 256
    return (hi + lo) / 64 - 273.15


def extract_temps_from_heatmap(mask: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
    """
    Fallback: estimate temperature proxy from blue channel of JET heatmap.
    Used when raw thdata is not available (e.g. testing on saved video).
    High blue → cool; we invert so higher value = warmer.
    """
    b_channel  = heatmap[:, :, 0]
    region_pix = b_channel[mask > 0].astype(np.float32)
    # Map 0-255 blue to a rough temp range (tweak to your scene)
    return 40.0 - (region_pix / 255.0) * 30.0


# ── Classifier ────────────────────────────────────────────────────────────────

def classify_fruit(region: FruitRegion,
                   heatmap: np.ndarray,
                   thdata: np.ndarray = None) -> ClassifiedFruit:
    """
    Classify a single fruit region using the MAD rule:

        sum( |T_i - T_avg| ) / N  >  MAD_THRESHOLD  →  Bad
                                   <=  MAD_THRESHOLD  →  Good

    Args:
        region  : FruitRegion from detector
        heatmap : BGR colormap frame (used as fallback if no thdata)
        thdata  : raw thermal bytes (SPLIT x WIDTH x 2), optional
    """
    if thdata is not None:
        temps = extract_temps_from_thdata(region.mask, thdata, heatmap.shape[:2])
    else:
        temps = extract_temps_from_heatmap(region.mask, heatmap)

    if len(temps) == 0:
        return ClassifiedFruit(region=region, temps=temps,
                               t_avg=0.0, mad=0.0, label="Bad")

    t_avg = float(np.mean(temps))
    mad   = float(np.sum(np.abs(temps - t_avg)) / len(temps))
    label = "Bad" if mad > MAD_THRESHOLD else "Good"

    return ClassifiedFruit(
        region = region,
        temps  = temps,
        t_avg  = round(t_avg, 2),
        mad    = round(mad, 3),
        label  = label,
    )


def classify_all(fruits: List[FruitRegion],
                 heatmap: np.ndarray,
                 thdata: np.ndarray = None) -> List[ClassifiedFruit]:
    """Run classifier on all detected fruit regions."""
    return [classify_fruit(f, heatmap, thdata) for f in fruits]


# ── Visualization ─────────────────────────────────────────────────────────────

def draw_results(frame: np.ndarray,
                 results: List[ClassifiedFruit]) -> np.ndarray:
    """
    Draw bounding boxes, labels and MAD values on frame.
      Green = Good
      Red   = Bad
    """
    vis = frame.copy()

    for r in results:
        color = (0, 255, 80) if r.label == "Good" else (0, 0, 255)
        x, y, w, h = r.region.bbox

        cv2.drawContours(vis, [r.region.contour], -1, color, 2)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 1)

        lines = [
            r.label,
            f"MAD={r.mad:.2f}C",
            f"Tavg={r.t_avg:.1f}C",
        ]
        for i, line in enumerate(lines):
            cv2.putText(vis, line, (x, y - 8 - i * 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    return vis