import logging
import sys
import time
import threading
from collections import deque
import cv2
import uvicorn
from config import settings
import database
from tracker import PersonTracker
from posture import analyze_posture, PostureState
from state_machine import FallStateMachine
from alert import trigger_alert
from api import app, set_latest_frame

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fall_detection.main")

# Skeleton connection pairs for YOLOv11 Pose (17 keypoints)
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4), # Face
    (5, 6),                         # Shoulders
    (5, 7), (7, 9),                 # Left arm
    (6, 8), (8, 10),                # Right arm
    (11, 12),                       # Hips
    (5, 11), (6, 12),               # Torso (shoulders to hips)
    (11, 13), (13, 15),             # Left leg
    (12, 14), (14, 16)              # Right leg
]

def draw_skeleton(frame, keypoints, keypoints_conf, confidence_threshold=0.5):
    """
    Draws the pose skeleton on the frame.
    """
    # Draw connections
    for pt1_idx, pt2_idx in SKELETON_CONNECTIONS:
        if keypoints_conf[pt1_idx] > confidence_threshold and keypoints_conf[pt2_idx] > confidence_threshold:
            x1, y1 = int(keypoints[pt1_idx][0]), int(keypoints[pt1_idx][1])
            x2, y2 = int(keypoints[pt2_idx][0]), int(keypoints[pt2_idx][1])
            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
    # Draw keypoint dots
    for idx, (x, y) in enumerate(keypoints):
        if keypoints_conf[idx] > confidence_threshold:
            cv2.circle(frame, (int(x), int(y)), 4, (0, 165, 255), -1) # Orange dots
class EventRecorder:
    def __init__(self, filepath, fps, width, height, pre_event_frames):
        self.filepath = filepath
        self.fps = fps
        self.width = width
        self.height = height
        
        # Initialize VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        # Write pre-event history frames
        for frame in pre_event_frames:
            if frame is not None:
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                self.writer.write(frame)
                
        # Total frames to record (3 minutes)
        self.total_frames_to_record = settings.EVENT_RECORDING_DURATION * fps
        self.frames_recorded = 0
        self.is_active = True
        
    def write_frame(self, frame):
        if not self.is_active:
            return
            
        if frame is not None:
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))
            self.writer.write(frame)
            self.frames_recorded += 1
            
        if self.frames_recorded >= self.total_frames_to_record:
            self.release()
            
    def release(self):
        if self.is_active:
            self.writer.release()
            self.is_active = False
            logger.info(f"Finished real-time event recording: {self.filepath}")

import os
import numpy as np

def process_video_stream():
    """
    Background worker thread that reads video frames, runs detection, tracking,
    posture analysis, state machine, motionless verification, and updates the streaming feed.
    """
    logger.info("Initializing video stream processing...")
    
    # Initialize components
    try:
        tracker = PersonTracker()
        state_machine = FallStateMachine()
    except Exception as e:
        logger.error(f"Failed to initialize tracker or detector: {e}")
        return

    # Determine video source
    source = settings.VIDEO_SOURCE
    if source.isdigit():
        source = int(source) # E.g., 0 for webcam
        
    cap = cv2.VideoCapture(source)
    simulation_mode = False
    
    if not cap.isOpened():
        logger.warning(f"Could not open video source '{source}'. Switching SentryPose AI to DEMO SIMULATION mode.")
        simulation_mode = True
        width = 640
        height = 480
        fps = settings.RECORDING_FPS
    else:
        # Fetch source dimensions and set recording parameters
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 60:
            fps = settings.RECORDING_FPS
        logger.info(f"Video source size: {width}x{height} @ {fps} FPS")

    # Frame buffer to save pre and post event clips
    buffer_seconds = settings.PRE_EVENT_BUFFER_DURATION + settings.POST_EVENT_BUFFER_DURATION
    buffer_size = int(buffer_seconds * fps)
    frame_buffer = deque(maxlen=buffer_size)
    
    frame_delay = 1.0 / fps
    sim_frame_count = 0
    
    active_recorders = []
    
    active_source = settings.VIDEO_SOURCE
    active_source_timestamp = settings.VIDEO_SOURCE_TIMESTAMP
    logger.info("Starting processing loop.")
    while True:
        # Check for dynamic video source change (including file overwrites)
        if settings.VIDEO_SOURCE != active_source or settings.VIDEO_SOURCE_TIMESTAMP != active_source_timestamp:
            logger.info(f"Video source updated to {settings.VIDEO_SOURCE}. Re-initializing video capture...")
            active_source = settings.VIDEO_SOURCE
            active_source_timestamp = settings.VIDEO_SOURCE_TIMESTAMP
            
            # Release old capture
            if not simulation_mode:
                cap.release()
                
            # Re-open capture
            cap = cv2.VideoCapture(active_source)
            if not cap.isOpened():
                logger.warning(f"Could not open new video source '{active_source}'. Switching to simulation mode.")
                simulation_mode = True
                width = 640
                height = 480
                fps = settings.RECORDING_FPS
            else:
                simulation_mode = False
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0 or fps > 60:
                    fps = settings.RECORDING_FPS
                logger.info(f"New video source size: {width}x{height} @ {fps} FPS")
                
            source = active_source
            
            # Reset buffers and state machine
            frame_buffer.clear()
            tracker = PersonTracker()
            state_machine = FallStateMachine()
            active_recorders = []
            
            # Reset frame delay
            frame_delay = 1.0 / fps
            continue

        start_time = time.time()
        
        if not simulation_mode:
            ret, frame = cap.read()
            if not ret:
                # If it's a file, loop back to the beginning for continuous demonstration
                if isinstance(source, str) and os.path.exists(source):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    logger.info("Video file ended. Looping back to start.")
                    continue
                else:
                    logger.warning("Failed to retrieve frame from video source. Reconnecting in 2s...")
                    cap.release()
                    time.sleep(2.0)
                    cap = cv2.VideoCapture(source)
                    continue
        else:
            # Generate simulated frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Draw floor
            cv2.line(frame, (0, 420), (width, 420), (50, 50, 50), 2)
            # Draw gird lines
            for x in range(0, width, 80):
                cv2.line(frame, (x, 0), (x, 420), (20, 20, 20), 1)
            for y in range(0, 420, 60):
                cv2.line(frame, (0, y), (width, y), (20, 20, 20), 1)
            
            # Print demo header
            cv2.putText(
                frame, 
                "DEMO MODE: SIMULATING CCTV CAM FEED", 
                (20, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (0, 165, 255), 
                1,
                cv2.LINE_AA
            )
            ret = True

        # Keep a copy of the raw frame in buffer
        frame_buffer.append(frame.copy())
        
        # Create an annotated frame for visualization
        annotated_frame = frame.copy()
        
        active_ids = []
        persons = []

        if not simulation_mode:
            # 1. Update Tracker (ByteTrack) using real detector
            persons = tracker.update(frame)
            active_ids = tracker.get_active_ids()
        else:
            # SIMULATION logic: Build coordinates for simulated subject #101
            track_id = 101
            active_ids = [track_id]
            
            cycle_len = 300
            cycle_idx = sim_frame_count % cycle_len
            
            # Simulated person state variables
            kp = np.zeros((17, 2), dtype=np.float32)
            kp_conf = np.ones(17, dtype=np.float32)
            
            if 0 <= cycle_idx < 80:
                # 1. Standing/Walking (VERTICAL)
                cx = 80 + int(cycle_idx * 2.5) # move horizontally
                cy = 280
                
                # Bbox
                bbox = [cx - 30, cy - 110, cx + 30, cy + 130]
                
                # Head
                kp[0] = [cx, cy - 100]
                # Shoulders
                kp[5] = [cx - 15, cy - 70]
                kp[6] = [cx + 15, cy - 70]
                # Hips
                kp[11] = [cx - 12, cy]
                kp[12] = [cx + 12, cy]
                # Ankles
                kp[15] = [cx - 10, cy + 120]
                kp[16] = [cx + 10, cy + 120]
                
            elif 80 <= cycle_idx < 95:
                # 2. Falling down (FALLING state transition)
                fall_pct = (cycle_idx - 80) / 15.0
                cx = 280 + int(fall_pct * 30)
                cy = 280 + int(fall_pct * 70)
                
                # Tilt angle
                angle_rad = fall_pct * (np.pi / 2.2) # ~80 degree tilt
                dx = int(80 * np.sin(angle_rad))
                dy = int(80 * np.cos(angle_rad))
                
                bbox = [cx - 80, cy - 80, cx + 80, cy + 85]
                
                kp[0] = [cx - dx, cy - dy - 20]
                kp[5] = [cx - dx - 10, cy - dy]
                kp[6] = [cx - dx + 10, cy - dy]
                kp[11] = [cx + dx - 10, cy + dy]
                kp[12] = [cx + dx + 10, cy + dy]
                kp[15] = [cx + dx + 15, cy + dy + 30]
                kp[16] = [cx + dx + 25, cy + dy + 30]
                
            elif 95 <= cycle_idx < 210:
                # 3. Lying still on floor (HORIZONTAL state)
                cx = 320
                cy = 380
                
                bbox = [cx - 120, cy - 35, cx + 120, cy + 35]
                
                kp[0] = [cx - 105, cy]
                kp[5] = [cx - 80, cy - 10]
                kp[6] = [cx - 80, cy + 10]
                kp[11] = [cx + 80, cy - 10]
                kp[12] = [cx + 80, cy + 10]
                kp[15] = [cx + 110, cy]
                kp[16] = [cx + 115, cy]
                
            elif 210 <= cycle_idx < 240:
                # 4. Recovering/Getting Up
                up_pct = (cycle_idx - 210) / 30.0
                cx = 320 + int(up_pct * 40)
                cy = 380 - int(up_pct * 100)
                
                angle_rad = (1.0 - up_pct) * (np.pi / 2.2)
                dx = int(80 * np.sin(angle_rad))
                dy = int(80 * np.cos(angle_rad))
                
                bbox = [cx - 50, cy - 90, cx + 50, cy + 90]
                
                kp[0] = [cx - dx, cy - dy - 20]
                kp[5] = [cx - dx - 10, cy - dy]
                kp[6] = [cx - dx + 10, cy - dy]
                kp[11] = [cx + dx - 10, cy + dy]
                kp[12] = [cx + dx + 10, cy + dy]
                kp[15] = [cx + dx + 15, cy + dy + 30]
                kp[16] = [cx + dx + 25, cy + dy + 30]
                
            else:
                # 5. Walk away (VERTICAL)
                walk_idx = cycle_idx - 240
                cx = 360 + int(walk_idx * 4.0)
                cy = 280
                
                bbox = [cx - 30, cy - 110, cx + 30, cy + 130]
                
                kp[0] = [cx, cy - 100]
                kp[5] = [cx - 15, cy - 70]
                kp[6] = [cx + 15, cy - 70]
                kp[11] = [cx - 12, cy]
                kp[12] = [cx + 12, cy]
                kp[15] = [cx - 10, cy + 120]
                kp[16] = [cx + 10, cy + 120]
                
            # If coordinates are within boundaries, add person
            if cx < width + 100:
                persons.append({
                    "track_id": track_id,
                    "bbox": bbox,
                    "keypoints": kp,
                    "keypoints_conf": kp_conf
                })
                
            sim_frame_count += 1
        
        # 2. Iterate through detected persons
        for person in persons:
            track_id = person["track_id"]
            bbox = person["bbox"]
            keypoints = person["keypoints"]
            kp_conf = person["keypoints_conf"]
            
            # Analyze Posture (Vertical, Falling, Horizontal)
            state, angle, aspect_ratio = analyze_posture(bbox, keypoints, kp_conf, track_id)
            
            # Filter out static objects (like chairs) to clean up visual overlays,
            # but NEVER hide people who are currently lying down (HORIZONTAL) or falling (FALLING)
            state_obj = state_machine.states.get(track_id)
            if state_obj and (time.time() - state_obj.position_history[0][0]) > 5.0 and state_obj.max_displacement < 20.0:
                if state not in [PostureState.HORIZONTAL, PostureState.FALLING]:
                    continue
            
            # Draw skeleton overlays
            draw_skeleton(annotated_frame, keypoints, kp_conf)
            
            # Choose color based on state
            if state == PostureState.VERTICAL:
                color = (0, 255, 0)  # Green
            elif state == PostureState.FALLING:
                color = (0, 165, 255) # Orange
            else: # HORIZONTAL
                color = (0, 0, 255)  # Red
                
            # Draw Bounding Box
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw Labels
            angle_str = f"Angle: {angle:.1f}" if angle is not None else "Angle: N/A"
            label = f"ID:{track_id} | {state} | {angle_str}"
            cv2.putText(
                annotated_frame, 
                label, 
                (x1, max(15, y1 - 8)), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                color, 
                2
            )
            
            # 3. Update Fall Detection State Machine
            alert_triggered, confidence, event_details = state_machine.update(
                track_id=track_id,
                posture=state,
                bbox=bbox,
                keypoints=keypoints,
                current_time=time.time(),
                frame=annotated_frame
            )
            
            # 4. Trigger Alert if a fall is confirmed
            if alert_triggered:
                # Add alert visual indicator overlay
                # Draw a large notification banner on top of the screenshot
                banner = annotated_frame.copy()
                cv2.rectangle(banner, (0, 0), (width, 60), (0, 0, 255), -1)
                cv2.addWeighted(banner, 0.7, annotated_frame, 0.3, 0, annotated_frame)
                
                alert_text = f"*** CRITICAL: FALL DETECTED (ID {track_id}, CONFIDENCE {confidence:.2f}) ***"
                cv2.putText(
                    annotated_frame, 
                    alert_text, 
                    (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (255, 255, 255), 
                    2,
                    cv2.LINE_AA
                )
                
                # Execute alert in real-time recording mode
                event_data = trigger_alert(
                    person_id=track_id,
                    confidence=confidence,
                    annotated_frame=annotated_frame,
                    video_frames=[],
                    details=event_details,
                    is_realtime_recording=True
                )
                
                # Retrieve the filename from generated path and setup active recording
                if settings.SAVE_VIDEO_ENABLED and event_data and event_data.get("video_path"):
                    video_filename = os.path.basename(event_data["video_path"])
                    abs_video_path = str(settings.VIDEOS_DIR / video_filename)
                    
                    recorder = EventRecorder(
                        filepath=abs_video_path,
                        fps=fps,
                        width=width,
                        height=height,
                        pre_event_frames=list(frame_buffer)
                    )
                    active_recorders.append(recorder)
                
        # Check for inactive alerts (fainted people whose track got lost)
        inactive_alerts = state_machine.check_inactive_alerts(active_ids, current_time=time.time())
        for track_id, confidence, event_details, last_falling_frame in inactive_alerts:
            # Use the frame when they were actually falling/horizontal if available, otherwise fallback to current frame
            base_frame = last_falling_frame if last_falling_frame is not None else annotated_frame
            alert_frame = base_frame.copy()
            
            banner = alert_frame.copy()
            cv2.rectangle(banner, (0, 0), (width, 60), (0, 0, 255), -1)
            cv2.addWeighted(banner, 0.7, alert_frame, 0.3, 0, alert_frame)
            
            alert_text = f"*** CRITICAL: FAINT DETECTED (ID {track_id}, CONFIDENCE {confidence:.2f} - LOST TRACK) ***"
            cv2.putText(
                alert_frame, 
                alert_text, 
                (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (255, 255, 255), 
                2,
                cv2.LINE_AA
            )
            
            trigger_alert(
                person_id=track_id,
                confidence=confidence,
                annotated_frame=alert_frame,
                video_frames=[],
                details=event_details,
                is_realtime_recording=True
            )
                
        # Clean up history for tracks that left the frame
        state_machine.clean_inactive_tracks(active_ids)
        
        # Write frames to any active real-time recorders
        for recorder in active_recorders:
            recorder.write_frame(annotated_frame)
            
        # Filter out inactive recorders
        active_recorders = [r for r in active_recorders if r.is_active]
        
        # 5. Push latest annotated frame to the API stream
        set_latest_frame(annotated_frame)
        
        # Maintain consistent frame rate processing speed
        elapsed = time.time() - start_time
        sleep_time = max(0.001, frame_delay - elapsed)
        time.sleep(sleep_time)
        
    if not simulation_mode:
        cap.release()
    logger.info("Video capture released.")

def main():
    # 1. Initialize PostgreSQL database
    logger.info("Initializing database...")
    database.init_db()
    
    # 2. Start video processing thread as a background worker
    video_thread = threading.Thread(target=process_video_stream, daemon=True)
    video_thread.start()
    
    # 3. Start FastAPI server using Uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8015)

if __name__ == "__main__":
    main()
