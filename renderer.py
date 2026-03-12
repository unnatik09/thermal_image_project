import cv2
import numpy as np

from camera      import SPLIT, WIDTH
from temperature import TempReader
from recorder    import Recorder, DISPLAY_W, DISPLAY_H
from detector    import detect_fruits
from classifier  import classify_all, draw_results

COLORMAP    = cv2.COLORMAP_JET
BTN_H       = 36
BTN_MARGIN  = 8
BTN_RADIUS  = 6

BUTTONS = [
    {'id': 'record', 'label': '[ REC ]',    'key': 'r'},
    {'id': 'stop',   'label': '[ STOP ]',   'key': 't'},
    {'id': 'detect', 'label': '[ DETECT ]', 'key': 'd'},
    {'id': 'snap',   'label': '[ SNAP ]',   'key': 'p'},
    {'id': 'export', 'label': '[ CSV ]',    'key': 'e'},
    {'id': 'quit',   'label': '[ QUIT ]',   'key': 'q'},
]


# ── Button Drawing ────────────────────────────────────────────────────────────

def _btn_color(btn_id: str, recorder, detect: bool):
    if btn_id == 'record':
        return (0, 0, 200) if not recorder.recording else (0, 0, 120)
    if btn_id == 'stop':
        return (0, 120, 200) if recorder.recording else (60, 60, 60)
    if btn_id == 'detect':
        return (0, 180, 0) if detect else (60, 60, 60)
    if btn_id == 'snap':
        return (180, 100, 0)
    if btn_id == 'export':
        return (150, 80, 150)
    if btn_id == 'quit':
        return (30, 30, 30)
    return (60, 60, 60)


def _draw_rounded_rect(img, x1, y1, x2, y2, color, radius=6, thickness=-1):
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    for cx, cy in [(x1+radius, y1+radius), (x2-radius, y1+radius),
                   (x1+radius, y2-radius), (x2-radius, y2-radius)]:
        cv2.circle(img, (cx, cy), radius, color, thickness)


def compute_button_rects(num_buttons: int):
    """Compute button bounding boxes along the bottom of the frame."""
    total_w   = DISPLAY_W - BTN_MARGIN * (num_buttons + 1)
    btn_w     = total_w // num_buttons
    rects     = []
    y1        = DISPLAY_H - BTN_H - BTN_MARGIN
    y2        = DISPLAY_H - BTN_MARGIN
    for i in range(num_buttons):
        x1 = BTN_MARGIN + i * (btn_w + BTN_MARGIN)
        x2 = x1 + btn_w
        rects.append((x1, y1, x2, y2))
    return rects


def draw_buttons(heatmap, recorder: Recorder, detect: bool):
    rects = compute_button_rects(len(BUTTONS))

    for btn, (x1, y1, x2, y2) in zip(BUTTONS, rects):
        bg    = _btn_color(btn['id'], recorder, detect)
        label = btn['label']

        # Semi-transparent background
        overlay = heatmap.copy()
        _draw_rounded_rect(overlay, x1, y1, x2, y2, bg, BTN_RADIUS)
        cv2.addWeighted(overlay, 0.75, heatmap, 0.25, 0, heatmap)

        # Border
        _draw_rounded_rect(heatmap, x1, y1, x2, y2, (200, 200, 200), BTN_RADIUS, 1)

        # Label — centered in button
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        tx = x1 + (x2 - x1 - tw) // 2
        ty = y1 + (y2 - y1 + th) // 2
        cv2.putText(heatmap, label, (tx + 1, ty + 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(heatmap, label, (tx, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # REC indicator
    if recorder.recording:
        cv2.circle(heatmap, (DISPLAY_W - 16, 16), 8, (0, 0, 255), -1)
        cv2.putText(heatmap, f"REC {recorder.elapsed}", (DISPLAY_W - 110, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(heatmap, f"REC {recorder.elapsed}", (DISPLAY_W - 110, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)


def get_clicked_button(x: int, y: int) -> str | None:
    """Return button id if (x, y) falls inside a button, else None."""
    rects = compute_button_rects(len(BUTTONS))
    for btn, (x1, y1, x2, y2) in zip(BUTTONS, rects):
        if x1 <= x <= x2 and y1 <= y <= y2:
            return btn['id']
    return None


# ── Main Render ───────────────────────────────────────────────────────────────

def render(imdata, thdata, temp_reader: TempReader,
           recorder: Recorder, detect: bool = True) -> np.ndarray:

    bgr     = cv2.cvtColor(imdata, cv2.COLOR_YUV2BGR_YUYV)
    bgr     = cv2.resize(bgr, (DISPLAY_W, DISPLAY_H), interpolation=cv2.INTER_CUBIC)
    heatmap = cv2.applyColorMap(bgr, COLORMAP)

    if detect:
        fruits  = detect_fruits(heatmap)
        results = classify_all(fruits, heatmap, thdata)
        heatmap = draw_results(heatmap, results)

    _draw_center_crosshair(heatmap, thdata, temp_reader)
    _draw_mouse_temp(heatmap, temp_reader)
    draw_buttons(heatmap, recorder, detect)

    return heatmap


def _draw_center_crosshair(heatmap, thdata, temp_reader: TempReader):
    temp   = temp_reader.decode(thdata, SPLIT // 2, WIDTH // 2)
    cx, cy = DISPLAY_W // 2, DISPLAY_H // 2
    cv2.line(heatmap, (cx, cy + 20), (cx, cy - 20), (255, 255, 255), 2)
    cv2.line(heatmap, (cx + 20, cy), (cx - 20, cy), (255, 255, 255), 2)
    cv2.putText(heatmap, f"{temp} C", (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)


def _draw_mouse_temp(heatmap, temp_reader: TempReader):
    mx, my = temp_reader.mx, temp_reader.my
    cv2.putText(heatmap, f"{temp_reader.current_temp} C", (mx + 10, my - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.circle(heatmap, (mx, my), 5, (255, 255, 255), 1)