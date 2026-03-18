import cv2

from camera      import ThermalCamera
from temperature import TempReader
from recorder    import Recorder, DISPLAY_W, DISPLAY_H
from renderer    import _draw_center_crosshair, _draw_mouse_temp, draw_buttons, get_clicked_button
from detector    import detect_fruits
from classifier  import classify_all, draw_results
from utils_for_ui.snapshot import save_snapshot
from utils_for_ui.settings import Settings

WINDOW_NAME = 'TC001 Thermal Scanner'


def on_mouse(event, x, y, flags, param):
    temp_reader, recorder, state = param
    temp_reader.on_mouse(event, x, y, flags, None)

    if event == cv2.EVENT_LBUTTONDOWN:
        btn = get_clicked_button(x, y)
        if btn == 'record'  and not recorder.recording: recorder.start_recording()
        elif btn == 'stop'  and recorder.recording:     recorder.stop_recording()
        elif btn == 'detect': state['detect'] = not state['detect']
        elif btn == 'snap':   state['snap']   = True
        elif btn == 'quit':   state['quit']   = True


def main():
    settings = Settings.load()
    camera   = ThermalCamera(index=1)
    temp     = TempReader()
    recorder = Recorder()
    state    = {'detect': True, 'quit': False, 'snap': False}

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, param=(temp, recorder, state))

    while not state['quit']:
        imdata, thdata = camera.read()
        if imdata is None:
            print("[Main] Stream ended.")
            break

        temp.update_thdata(thdata)

        bgr     = cv2.cvtColor(imdata, cv2.COLOR_YUV2BGR_YUYV)
        bgr     = cv2.resize(bgr, (DISPLAY_W, DISPLAY_H), interpolation=cv2.INTER_CUBIC)
        heatmap = cv2.applyColorMap(bgr, cv2.COLORMAP_JET)

        if state['detect']:
            fruits  = detect_fruits(heatmap)
            results = classify_all(fruits, heatmap, thdata)
            heatmap = draw_results(heatmap, results)

        _draw_center_crosshair(heatmap, thdata, temp)
        _draw_mouse_temp(heatmap, temp)
        draw_buttons(heatmap, recorder, state['detect'])

        recorder.write(heatmap)
        cv2.imshow(WINDOW_NAME, heatmap)

        if state['snap']:
            save_snapshot(heatmap, output_dir=settings.snapshot_dir)
            state['snap'] = False

        key = cv2.waitKey(1) & 0xFF
        if key == ord('r') and not recorder.recording: recorder.start_recording()
        if key == ord('t') and recorder.recording:     recorder.stop_recording()
        if key == ord('d'): state['detect'] = not state['detect']
        if key == ord('p'): save_snapshot(heatmap, output_dir=settings.snapshot_dir)
        if key == ord('q'): break

    camera.release()
    recorder.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()