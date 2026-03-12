import cv2

from camera import ThermalCamera
from temperature import TempReader, SCALE
from recorder import Recorder, DISPLAY_W, DISPLAY_H

# ── Constants ─────────────────────────────────────────────────────────────────

CAMERA_INDEX = 0
COLORMAP = cv2.COLORMAP_JET
WINDOW_NAME = 'TC001 Thermal Scanner'


# ── Renderer ──────────────────────────────────────────────────────────────────

def render(imdata, thdata, temp_reader, recorder):
    """Build the final display frame with heatmap, crosshair and HUD overlays."""

    # Convert YUV -> BGR -> colormap
    bgr     = cv2.cvtColor(imdata, cv2.COLOR_YUV2BGR_YUYV)
    bgr     = cv2.resize(bgr, (DISPLAY_W, DISPLAY_H), interpolation=cv2.INTER_CUBIC)
    heatmap = cv2.applyColorMap(bgr, COLORMAP)

    _draw_center_crosshair(heatmap, thdata, temp_reader)
    _draw_mouse_temp(heatmap, temp_reader)
    _draw_hud(heatmap, recorder)

    return heatmap


def _draw_center_crosshair(heatmap, thdata, temp_reader):
    from camera import SPLIT, WIDTH
    temp = temp_reader.decode(thdata, SPLIT // 2, WIDTH // 2)
    cx, cy = DISPLAY_W // 2, DISPLAY_H // 2

    cv2.line(heatmap, (cx, cy + 20), (cx, cy - 20), (255, 255, 255), 2)
    cv2.line(heatmap, (cx + 20, cy), (cx - 20, cy), (255, 255, 255), 2)
    cv2.putText(heatmap, f"{temp} C", (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)


def _draw_mouse_temp(heatmap, temp_reader):
    mx, my = temp_reader.mx, temp_reader.my
    cv2.putText(heatmap, f"{temp_reader.current_temp} C", (mx + 10, my - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.circle(heatmap, (mx, my), 5, (255, 255, 255), 1)


def _draw_hud(heatmap, recorder):
    if recorder.recording:
        cv2.putText(heatmap, f"REC {recorder.elapsed}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.circle(heatmap, (DISPLAY_W - 20, 20), 8, (0, 0, 255), -1)
    else:
        cv2.putText(heatmap, "r: Record | t: Stop | q: Quit", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    camera   = ThermalCamera(index=CAMERA_INDEX)
    temp     = TempReader()
    recorder = Recorder()

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, temp.on_mouse)

    while True:
        imdata, thdata = camera.read()
        if imdata is None:
            print("[Main] Stream ended.")
            break

        temp.update_thdata(thdata)

        heatmap = render(imdata, thdata, temp, recorder)
        recorder.write(heatmap)

        cv2.imshow(WINDOW_NAME, heatmap)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('r') and not recorder.recording:
            recorder.start_recording()
        if key == ord('t') and recorder.recording:
            recorder.stop_recording()
        if key == ord('q'):
            break

    # Cleanup
    camera.release()
    recorder.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()