import cv2
import os
import subprocess
import sys

camera_ip = "192.168.50.105"
url_encoded = "rtsp://swguser:Swguser789%23@192.168.50.105:554/Streaming/Channels/101"
url_literal = "rtsp://swguser:Swguser789#@192.168.50.105:554/Streaming/Channels/101"

print("=" * 60)
print("             CAMERA RTSP DIAGNOSTIC TOOL")
print("=" * 60)

# Step 1: Check Network Ping
print(f"\n[1/4] Checking network ping to {camera_ip}...")
ping_cmd = ["ping", "-c", "2", "-W", "2", camera_ip]
try:
    result = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        print(f"  SUCCESS: {camera_ip} is reachable via network ping!")
        print(result.stdout.strip())
    else:
        print(f"  WARNING: {camera_ip} did not respond to ping.")
        print("  Make sure your computer can route to the 192.168.50.x subnet.")
except Exception as e:
    print(f"  Error running ping: {e}")

# Step 2: Test URL Encoded
print(f"\n[2/4] Testing connection with URL-Encoded Password (%23)...")
cap = cv2.VideoCapture(url_encoded)
if cap.isOpened():
    ret, frame = cap.read()
    print("  SUCCESS: Connected using URL-encoded password!")
    print(f"  Frame resolution: {frame.shape[1]}x{frame.shape[0]}")
    cap.release()
else:
    print("  FAILED to connect using URL-encoded password (%23).")

# Step 3: Test URL Literal
print(f"\n[3/4] Testing connection with Literal Password (#)...")
cap = cv2.VideoCapture(url_literal)
if cap.isOpened():
    ret, frame = cap.read()
    print("  SUCCESS: Connected using literal password!")
    print(f"  Frame resolution: {frame.shape[1]}x{frame.shape[0]}")
    cap.release()
else:
    print("  FAILED to connect using literal password (#).")

# Step 4: Test with forced TCP transport
print(f"\n[4/4] Testing connection forcing TCP transport...")
# For OpenCV, we can set environment variable to force TCP for FFmpeg
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
cap = cv2.VideoCapture(url_encoded)
if cap.isOpened():
    ret, frame = cap.read()
    print("  SUCCESS: Connected forcing TCP transport!")
    cap.release()
else:
    print("  FAILED to connect forcing TCP transport.")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
