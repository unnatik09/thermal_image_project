import cv2

from camera      import ThermalCamera
from temperature import TempReader
from recorder    import Recorder
from renderer    import render, get_clicked_button

CAMERA_INDEX = 0
WINDOW_NAME  = 'TC001 Thermal Scanner'


def handle_button(btn_id: str, recorder: Recorder, detect: bool) -> bool:
    """Handle button click or keypress. Returns updated detect state."""
    if btn_id == 'record' and not recorder.recording:
        recorder.start_recording()
    elif btn_id == 'stop' and recorder.recording:
        recorder.stop_recording()
    elif btn_id == 'detect':
        detect = not detect
        print(f"[Main] Detection {'ON' if detect else 'OFF'}")
    elif btn_id == 'quit':
        return None   # signal quit
    return detect


def on_mouse(event, x, y, flags, param):
    """Handle both mouse temp tracking and button clicks."""
    temp_reader, recorder, state = param
    temp_reader.on_mouse(event, x, y, flags, None)

    if event == cv2.EVENT_LBUTTONDOWN:
        btn = get_clicked_button(x, y)
        if btn:
            result = handle_button(btn, recorder, state['detect'])
            if result is None:
                state['quit'] = True
            else:
                state['detect'] = result


def main():
    camera   = ThermalCamera(index=CAMERA_INDEX)
    temp     = TempReader()
    recorder = Recorder()
    state    = {'detect': True, 'quit': False}

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, param=(temp, recorder, state))

    while True:
        if state['quit']:
            break

        imdata, thdata = camera.read()
        if imdata is None:
            print("[Main] Stream ended.")
            break

        temp.update_thdata(thdata)
        heatmap = render(imdata, thdata, temp, recorder, detect=state['detect'])
        recorder.write(heatmap)
        cv2.imshow(WINDOW_NAME, heatmap)

        key = cv2.waitKey(1) & 0xFF
        key_map = {ord('r'): 'record', ord('t'): 'stop',
                   ord('d'): 'detect', ord('q'): 'quit'}
        if key in key_map:
            result = handle_button(key_map[key], recorder, state['detect'])
            if result is None:
                break
            state['detect'] = result

    camera.release()
    recorder.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()