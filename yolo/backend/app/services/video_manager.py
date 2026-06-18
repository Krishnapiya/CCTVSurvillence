import os
import cv2
import uuid
import time
from collections import deque
from typing import Dict, List, Optional
import numpy as np
from app.core.config import settings

class VideoManager:
    def __init__(self):
        # Maps camera_id (str) to a deque of (timestamp, jpeg_bytes)
        self.buffers: Dict[str, deque] = {}
        # Maximum frames to keep. 5 seconds at ~15 fps = 75 frames.
        self.fps_target = 15
        self.maxlen = int(settings.PRE_TRIGGER_DURATION_SECS * self.fps_target)

    def add_frame(self, camera_id: str, frame: np.ndarray):
        """
        Compresses frame to JPEG and adds to the ring buffer.
        """
        if camera_id not in self.buffers:
            self.buffers[camera_id] = deque(maxlen=self.maxlen)

        try:
            # Compress to JPEG to save RAM (takes ~50KB instead of ~6MB per frame)
            success, encoded_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if success:
                self.buffers[camera_id].append((time.time(), encoded_img.tobytes()))
        except Exception as e:
            print(f"Error encoding frame for buffer: {e}")

    def save_pre_trigger_frames(self, camera_id: str, event_id: str) -> Optional[str]:
        """
        Saves all JPEG frames in the buffer to a temporary directory.
        Returns the path of the directory.
        """
        if camera_id not in self.buffers or len(self.buffers[camera_id]) == 0:
            return None

        temp_dir = os.path.join(settings.MEDIA_STORAGE_DIR, "temp", event_id)
        os.makedirs(temp_dir, exist_ok=True)

        frames_data = list(self.buffers[camera_id])
        for idx, (timestamp, jpeg_bytes) in enumerate(frames_data):
            frame_path = os.path.join(temp_dir, f"frame_{idx:05d}_{timestamp}.jpg")
            with open(frame_path, "wb") as f:
                f.write(jpeg_bytes)
        
        return temp_dir

    def get_buffer_size(self, camera_id: str) -> int:
        if camera_id in self.buffers:
            return len(self.buffers[camera_id])
        return 0

video_manager = VideoManager()
