import subprocess
import numpy as np
import cv2

WIDTH, HEIGHT = 256, 384
SPLIT = HEIGHT // 2  # 192

process = subprocess.Popen([
    'ffmpeg',
    '-f', 'avfoundation',
    '-video_size', f'{WIDTH}x{HEIGHT}',
    '-framerate', '25',
    '-i', '0',
    '-f', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-',
], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

frame_size = WIDTH * HEIGHT * 3

while True:
    raw = process.stdout.read(frame_size)
    if len(raw) != frame_size:
        print("Stream ended or error.")
        break

    frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 3))

    visual  = frame[0:SPLIT, :]       # top 192 rows — visual
    thermal = frame[SPLIT:HEIGHT, :]  # bottom 192 rows — thermal

    # Upscale both for visibility
    visual_big  = cv2.resize(visual,  (512, 384), interpolation=cv2.INTER_NEAREST)
    thermal_big = cv2.resize(thermal, (512, 384), interpolation=cv2.INTER_NEAREST)

    # Side by side
    combined = np.hstack([visual_big, thermal_big])

    cv2.imshow('TC001 — Visual | Thermal', combined)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

process.terminate()
cv2.destroyAllWindows()