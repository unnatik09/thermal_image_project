import subprocess
import numpy as np
import cv2
import time

WIDTH, HEIGHT = 256, 384
SPLIT = HEIGHT // 2
scale = 3
DISPLAY_W = WIDTH * scale
DISPLAY_H = SPLIT * scale

current_temp = 0.0
mx, my = 0, 0
recording = False
videoOut = None
elapsed = "00:00:00"
start = None

def get_temp(thdata, row, col):
    hi = int(thdata[row, col, 0])
    lo = int(thdata[row, col, 1]) * 256
    return round((hi + lo) / 64 - 273.15, 2)

def on_mouse(event, x, y, flags, param):
    global current_temp, mx, my
    if event == cv2.EVENT_MOUSEMOVE:
        mx, my = x, y
        thdata = param
        real_x = min(x // scale, WIDTH - 1)
        real_y = min(y // scale, SPLIT - 1)
        if 0 <= real_y < thdata.shape[0] and 0 <= real_x < thdata.shape[1]:
            current_temp = get_temp(thdata, real_y, real_x)

process = subprocess.Popen([
    'ffmpeg',
    '-f', 'avfoundation',
    '-video_size', f'{WIDTH}x{HEIGHT}',
    '-framerate', '25',
    '-i', '0',
    '-f', 'rawvideo',
    '-pix_fmt', 'yuyv422',
    '-',
], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

frame_size = WIDTH * HEIGHT * 2

cv2.namedWindow('TC001 Thermal Scanner')

while True:
    raw = process.stdout.read(frame_size)
    if len(raw) != frame_size:
        print("Stream ended or error.")
        break

    frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 2))

    imdata = frame[0:SPLIT, :]
    thdata = frame[SPLIT:HEIGHT, :]

    cv2.setMouseCallback('TC001 Thermal Scanner', on_mouse, param=thdata)

    yuv = imdata.reshape((SPLIT, WIDTH, 2))
    bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_YUYV)
    bgr = cv2.resize(bgr, (DISPLAY_W, DISPLAY_H), interpolation=cv2.INTER_CUBIC)
    heatmap = cv2.applyColorMap(bgr, cv2.COLORMAP_JET)

    # Center crosshair
    center_temp = get_temp(thdata, SPLIT // 2, WIDTH // 2)
    cx, cy = DISPLAY_W // 2, DISPLAY_H // 2
    cv2.line(heatmap, (cx, cy + 20), (cx, cy - 20), (255, 255, 255), 2)
    cv2.line(heatmap, (cx + 20, cy), (cx - 20, cy), (255, 255, 255), 2)
    cv2.putText(heatmap, f"{center_temp} C", (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

    # Mouse temp
    cv2.putText(heatmap, f"{current_temp} C", (mx + 10, my - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.circle(heatmap, (mx, my), 5, (255, 255, 255), 1)

    # Recording indicator
    if recording:
        elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time() - start))
        cv2.putText(heatmap, f"REC {elapsed}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.circle(heatmap, (DISPLAY_W - 20, 20), 8, (0, 0, 255), -1)  # red dot
        videoOut.write(heatmap)
    else:
        cv2.putText(heatmap, "r: Record | t: Stop | q: Quit", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)

    cv2.imshow('TC001 Thermal Scanner', heatmap)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('r') and not recording:
        now = time.strftime("%Y%m%d-%H%M%S")
        filename = f"TC001_{now}.avi"
        videoOut = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), 25, (DISPLAY_W, DISPLAY_H))
        recording = True
        start = time.time()
        print(f"Recording started: {filename}")

    if key == ord('t') and recording:
        recording = False
        videoOut.release()
        videoOut = None
        elapsed = "00:00:00"
        print("Recording stopped.")

    if key == ord('q'):
        break

if recording and videoOut:
    videoOut.release()

process.terminate()
cv2.destroyAllWindows()