import logging
import os
import json
import time
import subprocess
import threading
from datetime import datetime, timezone
import cv2
import numpy as np
from config import settings
import database

logger = logging.getLogger("fall_detection.alert")

def sound_alarm_async():
    """
    Play the alarm sound in a background thread so as not to block processing.
    """
    if not settings.SOUND_ALARM_ENABLED:
        return

    def play():
        sound_path = settings.ALARM_SOUND_PATH
        if not os.path.exists(sound_path):
            logger.warning(f"Alarm sound file not found: {sound_path}. Emitting beep instead.")
            # Fallback beep using system echo (or just log it)
            try:
                # ASCII bell character
                print('\a', end='', flush=True)
            except Exception:
                pass
            return
            
        try:
            logger.info("Triggering audio alarm...")
            # Try aplay first (default ALSA player on Linux)
            subprocess.run(["aplay", "-q", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            try:
                # Try paplay (PulseAudio player)
                subprocess.run(["paplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.error(f"Failed to play alarm sound using system players: {e}")

    threading.Thread(target=play, daemon=True).start()

def save_video_clip_thread(video_path: str, frames: list[np.ndarray], fps: int, width: int, height: int):
    """
    Worker function to write list of frames to a video file.
    """
    try:
        logger.info(f"Starting async video clip generation: {video_path}")
        
        # Use MP4V codec which is standard and works well on Linux
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        
        for frame in frames:
            # Check frame validity
            if frame is not None and frame.shape[0] == height and frame.shape[1] == width:
                out.write(frame)
                
        out.release()
        logger.info(f"Finished writing video clip: {video_path}")
    except Exception as e:
        logger.error(f"Error writing video clip to disk: {e}")

def trigger_alert(
    person_id: int, 
    confidence: float, 
    annotated_frame: np.ndarray, 
    video_frames: list[np.ndarray],
    details: dict,
    is_realtime_recording: bool = False
) -> dict:
    """
    Trigger a fall/fainting alert, saving media and logging to database.
    
    Args:
        person_id: Tracking ID of the person
        confidence: Confidence score of the detection [0.0, 1.0]
        annotated_frame: Image frame with visual bounding boxes and labels
        video_frames: History list of recent frames (raw BGR)
        details: Extra details of the fall (velocity, motion score, etc.)
        is_realtime_recording: If True, indicates video is being recorded dynamically on disk
        
    Returns:
        A dictionary containing the logged event information.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    iso_timestamp = datetime.now(timezone.utc).isoformat()
    
    # 1. Sound Alarm
    sound_alarm_async()
    
    # Define paths
    screenshot_filename = f"screenshot_{timestamp_str}_p{person_id}.jpg"
    screenshot_path = str(settings.EVENTS_DIR / screenshot_filename)
    
    if settings.SAVE_VIDEO_ENABLED:
        video_filename = f"clip_{timestamp_str}_p{person_id}.mp4"
        video_path = str(settings.VIDEOS_DIR / video_filename)
    else:
        video_filename = ""
        video_path = ""
    
    json_filename = f"event_{timestamp_str}_p{person_id}.json"
    json_path = str(settings.EVENTS_DIR / json_filename)
    
    # 2. Save Screenshot
    try:
        cv2.imwrite(screenshot_path, annotated_frame)
        logger.info(f"Screenshot saved to: {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        screenshot_path = ""
        
    # 3. Save Video Clip (Async)
    if not settings.SAVE_VIDEO_ENABLED:
        logger.info("Video saving is disabled by user settings.")
    elif is_realtime_recording:
        logger.info(f"Real-time background recording started for video: {video_path}")
    elif video_frames and len(video_frames) > 0:
        h, w = video_frames[0].shape[:2]
        # Copy frames to avoid race conditions with main video loop
        frames_copy = [f.copy() for f in video_frames if f is not None]
        threading.Thread(
            target=save_video_clip_thread,
            args=(video_path, frames_copy, settings.RECORDING_FPS, w, h),
            daemon=True
        ).start()
    else:
        logger.warning("No video frames available to generate event clip.")
        video_path = ""

    # Prepare event data
    event_data = {
        "person_id": person_id,
        "timestamp": iso_timestamp,
        "confidence_score": confidence,
        "screenshot_path": f"/events/{screenshot_filename}" if screenshot_path else "",
        "video_path": f"/videos/{video_filename}" if video_path else "",
        "details": details
    }
    
    # 4. Save JSON record
    try:
        with open(json_path, 'w') as f:
            json.dump(event_data, f, indent=4)
        logger.info(f"JSON event metadata saved to: {json_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON event metadata: {e}")

    # 5. Log to PostgreSQL
    event_id = database.save_event(
        person_id=person_id,
        confidence_score=confidence,
        screenshot_path=event_data["screenshot_path"],
        video_path=event_data["video_path"],
        details=details
    )
    
    event_data["event_id"] = event_id
    return event_data
