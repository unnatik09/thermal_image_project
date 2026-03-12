import cv2
import numpy as np

current_temp = 0.0
mx, my = 0, 0


def on_mouse(event, x, y, flags, param):
    global current_temp, mx, my
    if event == cv2.EVENT_MOUSEMOVE:
        # Scale back down from the 3x display to the 192x256 data grid
        real_x, real_y = x // 3, y // 3
        mx, my = x, y

        thdata = param
        if real_y < thdata.shape[0] and real_x < thdata.shape[1]:
            # DATA EXTRACTION
            hi = thdata[real_y, real_x, 0]
            lo = thdata[real_y, real_x, 1].astype(np.uint16) * 256
            current_temp = round(((hi + lo) / 64) - 273.15, 2)


# Mac usually maps the TC001 to index 1 or 2 (0 is the FaceTime HD Camera)
cap = cv2.VideoCapture(1)

# EXPLICITLY set the TC001 data resolution for macOS
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)

cv2.namedWindow('Mac_Thermal_Scanner')

while True:
    ret, frame = cap.read()
    if not ret: break

    # The TC001 sends a 256x384 image. Split it.
    # Top 192 pixels: Visual. Bottom 192 pixels: Data.
    visual, thdata = np.array_split(frame, 2)

    # Attach data to mouse callback
    cv2.setMouseCallback('Mac_Thermal_Scanner', on_mouse, param=thdata)

    # Upscale for your screen
    display = cv2.resize(visual, (256 * 3, 192 * 3), interpolation=cv2.INTER_NEAREST)
    display = cv2.applyColorMap(display, cv2.COLORMAP_MAGMA)

    # HUD
    cv2.putText(display, f"{current_temp} C", (mx + 10, my - 10),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
    cv2.circle(display, (mx, my), 5, (255, 255, 255), 1)

    cv2.imshow('Mac_Thermal_Scanner', display)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()