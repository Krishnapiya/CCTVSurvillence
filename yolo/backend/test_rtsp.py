import cv2
import sys

rtsp_url = "rtsp://swguser:Swguser789%23@192.168.50.105:554/Streaming/Channels/101"
print(f"Testing RTSP URL: {rtsp_url}")

cap = cv2.VideoCapture(rtsp_url)
opened = cap.isOpened()
print(f"cap.isOpened(): {opened}")

if opened:
    ret, frame = cap.read()
    print(f"cap.read() success: {ret}")
    if ret:
        print(f"Frame shape: {frame.shape}")
else:
    print("Could not open video capture.")

cap.release()
