import cv2
import time

from camera           import ThermalCamera
from temperature      import TempReader
from recorder         import Recorder, DISPLAY_W, DISPLAY_H
from renderer         import render, get_clicked_button
from detector         import detect_fruits
from classifier       import classify_all, draw_results
from utils_for_ui.logger       import DetectionLogger
from utils_for_ui.csv_exporter import export_to_csv
from utils_for_ui.snapshot     import save_snapshot
from utils_for_ui.settings     import Settings

WINDOW_NAME = 'TC001 Thermal Scanner'

# ── State ─────────────────────────────────────────────────────────────────────

settings   = Settings.load()
logger     = DetectionLogger()
frame_num  = 0


def log_detections(results, thdata):
    import numpy as np
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    for i, r in enumerate(results):
        temps = r.temps if len(r.temps) > 0 else np.array([0.0])
        logger.log(
            timestamp    = ts,
            frame_number = frame_num,
            fruit_id     = i + 1,
            label        = r.label,
            mad          = r.mad,
            t_avg        = r.t_avg,
            t_min        = round(float(temps.min()), 2),
            t_max        = round(float(temps.max()), 2),
            pixel_area   = r.region.area,
        )


# ── Mouse ─────────────────────────────────────────────────────────────────────

def on_mouse(event, x, y, flags, param):
    temp_reader, recorder, state = param
    temp_reader.on_mouse(event, x, y, flags, None)

    if event == cv2.EVENT_LBUTTONDOWN:
        btn = get_clicked_button(x, y)
        if btn == 'record'   and not recorder.recording: recorder.start_recording()
        elif btn == 'stop'   and recorder.recording:     recorder.stop_recording()
        elif btn == 'detect': state['detect'] = not state['detect']
        elif btn == 'snap':   state['snap']   = True
        elif btn == 'export': state['export'] = True
        elif btn == 'quit':   state['quit']   = True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global frame_num

    camera   = ThermalCamera(index=1)
    temp     = TempReader()
    recorder = Recorder()
    state    = {'detect': True, 'quit': False, 'snap': False, 'export': False}

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, param=(temp, recorder, state))

    while not state['quit']:
        imdata, thdata = camera.read()
        if imdata is None:
            print("[Main] Stream ended.")
            break

        frame_num += 1
        temp.update_thdata(thdata)

        # Build heatmap
        import cv2 as _cv2
        import numpy as np
        bgr     = _cv2.cvtColor(imdata, _cv2.COLOR_YUV2BGR_YUYV)
        bgr     = _cv2.resize(bgr, (DISPLAY_W, DISPLAY_H), interpolation=_cv2.INTER_CUBIC)
        heatmap = _cv2.applyColorMap(bgr, _cv2.COLORMAP_JET)

        # Detection + logging
        if state['detect']:
            fruits  = detect_fruits(heatmap)
            results = classify_all(fruits, heatmap, thdata)
            log_detections(results, thdata)
            heatmap = draw_results(heatmap, results)

        # Crosshair + buttons
        from renderer import _draw_center_crosshair, _draw_mouse_temp, draw_buttons
        _draw_center_crosshair(heatmap, thdata, temp)
        _draw_mouse_temp(heatmap, temp)
        draw_buttons(heatmap, recorder, state['detect'])

        recorder.write(heatmap)
        cv2.imshow(WINDOW_NAME, heatmap)

        # ── One-shot actions ──────────────────────────────────────────────────
        if state['snap']:
            save_snapshot(heatmap, output_dir=settings.snapshot_dir)
            state['snap'] = False

        if state['export']:
            export_to_csv(logger.entries)
            state['export'] = False

        # ── Keyboard ──────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r') and not recorder.recording: recorder.start_recording()
        if key == ord('t') and recorder.recording:     recorder.stop_recording()
        if key == ord('d'): state['detect'] = not state['detect']
        if key == ord('p'): save_snapshot(heatmap, output_dir=settings.snapshot_dir)
        if key == ord('e'): export_to_csv(logger.entries)
        if key == ord('q'): break

    # Auto export on quit
    if logger.entries:
        export_to_csv(logger.entries)

    camera.release()
    recorder.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()