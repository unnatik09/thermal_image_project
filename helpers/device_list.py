import subprocess
import numpy as np
import cv2

# First, list available devices
result = subprocess.run([
    'ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''
], capture_output=True, text=True)

print(result.stderr)