import os
import cv2
import numpy as np
import base64
import uuid
import subprocess
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any

from app.core.config import settings
from app.services.ai_engine import ai_engine

router = APIRouter()

SKELETON = [
    (5, 6), (5, 11), (6, 12), (11, 12), # shoulders, hips, torso
    (5, 7), (7, 9),                     # left arm
    (6, 8), (8, 10),                    # right arm
    (11, 13), (13, 15),                 # left leg
    (12, 14), (14, 16)                  # right leg
]

def draw_annotations(frame: np.ndarray, events: List[Dict[str, Any]]) -> np.ndarray:
    """Draw bounding boxes and text from AIEngine events on the frame."""
    draw_frame = frame.copy()
    h, w, _ = frame.shape
    
    for event in events:
        etype = event["type"]
        conf = event["confidence"]
        details = event["details"]
        
        # Color scheme
        if etype in ["fire", "smoke", "intrusion"]:
            color = (0, 0, 255) # Red
        elif etype == "fight":
            color = (0, 165, 255) # Orange
        elif etype in ["mobile_usage", "smoking"]:
            color = (255, 0, 255) # Purple
        else:
            color = (0, 255, 0) # Green
            
        # Draw bounding box
        if "bbox" in details:
            x1, y1, x2, y2 = details["bbox"]
            cv2.rectangle(draw_frame, (x1, y1), (x2, y2), color, 2)
            label = f"{etype.upper()} ({conf:.2f})"
            cv2.putText(draw_frame, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
        elif "bbox1" in details and "bbox2" in details: # Fight event (draw both boxes)
            for bbox in [details["bbox1"], details["bbox2"]]:
                x1, y1, x2, y2 = bbox
                cv2.rectangle(draw_frame, (x1, y1), (x2, y2), color, 2)
            label = f"FIGHT DETECTED ({conf:.2f})"
            x1, y1 = details["bbox1"][:2]
            cv2.putText(draw_frame, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
    # Draw Pose Keypoints/Skeleton
    # Lazy init of pose model if not done
    ai_engine._init_models()
    if ai_engine._pose_model is not None:
        pose_res = ai_engine._pose_model(frame, verbose=False)
        for r in pose_res:
            if r.keypoints is not None:
                for kps in r.keypoints:
                    xy = kps.xy[0].cpu().numpy()
                    conf = kps.conf[0].cpu().numpy() if kps.conf is not None else np.ones(len(xy))
                    
                    # Draw keypoints (yellow dots)
                    for idx, (x, y) in enumerate(xy):
                        if idx < len(conf) and conf[idx] > 0.4 and x > 0 and y > 0:
                            cv2.circle(draw_frame, (int(x), int(y)), 3, (0, 255, 255), -1)
                            
                    # Draw connections (cyan lines)
                    for p1, p2 in SKELETON:
                        if p1 < len(xy) and p2 < len(xy):
                            x1, y1 = xy[p1]
                            x2, y2 = xy[p2]
                            if p1 < len(conf) and p2 < len(conf) and min(conf[p1], conf[p2]) > 0.4:
                                if min(x1, x2) > 0 and min(y1, y2) > 0:
                                    cv2.line(draw_frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2)
                                    
    return draw_frame

@router.post("/image")
async def test_yolo_image(file: UploadFile = File(...)) -> Any:
    """Run YOLO models on uploaded image and return base64 output with event details."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
        
    # Run YOLO detections
    events = await ai_engine.detect_frame(camera_id="test_cam", frame=frame)
    
    # Annotate frame
    annotated_frame = draw_annotations(frame, events)
    
    # Encode to base64
    _, buffer = cv2.imencode(".jpg", annotated_frame)
    base64_str = base64.b64encode(buffer).decode("utf-8")
    
    return {
        "detections": events,
        "image": f"data:image/jpeg;base64,{base64_str}"
    }

@router.post("/video")
async def test_yolo_video(file: UploadFile = File(...)) -> Any:
    """Run YOLO on uploaded video (first 150 frames) and return play link."""
    temp_in_path = f"/tmp/test_in_{uuid.uuid4()}.mp4"
    temp_out_path = f"/tmp/test_out_{uuid.uuid4()}.mp4"
    
    # Save input video to temp
    with open(temp_in_path, "wb") as f:
        f.write(await file.read())
        
    cap = cv2.VideoCapture(temp_in_path)
    if not cap.isOpened():
        if os.path.exists(temp_in_path):
            os.remove(temp_in_path)
        raise HTTPException(status_code=400, detail="Invalid video file.")
        
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Define VideoWriter (temp raw format)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_out_path, fourcc, fps, (width, height))
    
    detected_types = set()
    frame_count = 0
    max_frames = 150 # Process first 6 seconds at 25 fps
    
    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Run detection
        events = await ai_engine.detect_frame(camera_id="test_cam", frame=frame)
        for ev in events:
            detected_types.add(ev["type"])
            
        # Draw on frame
        annotated_frame = draw_annotations(frame, events)
        out.write(annotated_frame)
        frame_count += 1
        
    cap.release()
    out.release()
    
    # Delete input temp file
    if os.path.exists(temp_in_path):
        os.remove(temp_in_path)
        
    # Convert output video to web-friendly H.264
    final_filename = f"processed_{uuid.uuid4()}.mp4"
    final_output_path = os.path.join(settings.MEDIA_STORAGE_DIR, final_filename)
    
    # Use FFMPEG to compile into H264 MP4 format for browser support
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", temp_out_path,
        "-vcodec", "libx264", "-pix_fmt", "yuv420p",
        "-profile:v", "baseline", "-level", "3.0",
        final_output_path
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # Delete raw temp out
        if os.path.exists(temp_out_path):
            os.remove(temp_out_path)
    except Exception as e:
        print(f"FFMPEG conversion failed: {e}. Falling back to raw MP4.")
        # Fallback to copy raw temp file directly
        import shutil
        shutil.move(temp_out_path, final_output_path)
        
    return {
        "video_url": f"/media/{final_filename}",
        "detected_types": list(detected_types),
        "processed_frames": frame_count
    }
