import cv2
import time
import datetime
import os
from config import SAVE_FOLDER


def capture_photo() -> str | None:
    """Capture a photo from the default webcam and save it to SAVE_FOLDER."""
    cam = cv2.VideoCapture(0)
    time.sleep(1)  # warm-up so the frame isn't black
    ret, frame = cam.read()
    cam.release()

    if not ret:
        print("[-] Webcam capture failed — no frame returned.")
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SAVE_FOLDER, f"intruder_{timestamp}.jpg")
    cv2.imwrite(path, frame)
    print(f"[+] Photo saved: {path}")
    return path
