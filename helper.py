import subprocess
import numpy as np
import cv2

WIDTH, HEIGHT = 256, 384
SPLIT = HEIGHT // 2  # 192
scale = 3

current_temp = 0.0
mx, my = 0, 0

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
    '-i', '1',
    '-f', 'rawvideo',
    '-pix_fmt', 'yuyv422',   # NO color conversion — preserve raw bytes
    '-',
], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

# yuyv422 = 2 bytes per pixel
frame_size = WIDTH * HEIGHT * 2

cv2.namedWindow('TC001 Thermal Scanner')

while True:
    raw = process.stdout.read(frame_size)
    if len(raw) != frame_size:
        print("Stream ended or error.")
        break

    # Shape as YUYV — 2 channels effectively, keep as (H, W, 2)
    frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 2))

    imdata = frame[0:SPLIT, :]       # top — visual (YUV)
    thdata = frame[SPLIT:HEIGHT, :]  # bottom — raw temp bytes

    cv2.setMouseCallback('TC001 Thermal Scanner', on_mouse, param=thdata)

    # Convert visual frame YUV -> BGR for display
    # YUYV needs to be treated as full YUV422
    yuv = imdata.reshape((SPLIT, WIDTH, 2))
    bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_YUYV)
    bgr = cv2.resize(bgr, (WIDTH * scale, SPLIT * scale), interpolation=cv2.INTER_CUBIC)
    heatmap = cv2.applyColorMap(bgr, cv2.COLORMAP_JET)

    # Center crosshair temp
    center_temp = get_temp(thdata, SPLIT // 2, WIDTH // 2)
    cx, cy = (WIDTH * scale) // 2, (SPLIT * scale) // 2
    cv2.line(heatmap, (cx, cy + 20), (cx, cy - 20), (255, 255, 255), 2)
    cv2.line(heatmap, (cx + 20, cy), (cx - 20, cy), (255, 255, 255), 2)
    cv2.putText(heatmap, f"{center_temp} C", (cx + 10, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

    # Mouse temp
    cv2.putText(heatmap, f"{current_temp} C", (mx + 10, my - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.circle(heatmap, (mx, my), 5, (255, 255, 255), 1)

    cv2.imshow('TC001 Thermal Scanner', heatmap)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

process.terminate()
cv2.destroyAllWindows()