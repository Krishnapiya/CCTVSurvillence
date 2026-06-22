import logging
import os
from pathlib import Path
from ultralytics import YOLO
import numpy as np
from config import settings

import torch

logger = logging.getLogger("fall_detection.detector")

class PoseDetector:
    def __init__(self):
        """
        Initialize the YOLOv11 Pose model.
        Downloads the model automatically if it is not present in the models/ directory.
        """
        model_path = settings.YOLO_MODEL_PATH
        logger.info(f"Loading YOLOv11 Pose model from: {model_path}")
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Determine device
        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info("CUDA GPU detected. Running YOLOv11 Pose on GPU (cuda).")
        else:
            self.device = "cpu"
            logger.info("CUDA GPU NOT detected. Running YOLOv11 Pose on CPU.")

        try:
            # YOLO(path) automatically downloads the model from Ultralytics if not found
            self.model = YOLO(model_path)
            self.model.to(self.device)
            logger.info("YOLOv11 Pose model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLOv11 Pose model: {e}")
            raise e

    def detect_and_track(self, frame: np.ndarray) -> list:
        """
        Runs YOLOv11 Pose estimation and tracking on the given frame.
        
        Args:
            frame: OpenCV image frame (BGR format).
            
        Returns:
            A list of dictionaries containing tracked person information:
            [
                {
                    "track_id": int,
                    "bbox": [x1, y1, x2, y2],
                    "box_conf": float,
                    "keypoints": np.ndarray of shape (17, 2),
                    "keypoints_conf": np.ndarray of shape (17,)
                },
                ...
            ]
        """
        # Run track using bytetrack
        try:
            results = self.model.track(
                source=frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=0.15,
                iou=0.5,
                verbose=False,
                device=self.device
            )
        except Exception as e:
            logger.error(f"Error running YOLOv11 Pose tracking: {e}")
            return []

        tracked_persons = []
        
        if not results or len(results) == 0:
            logger.info("Detections: 0")
            return tracked_persons
            
        result = results[0]
        
        # Check if boxes and keypoints are present
        if result.boxes is None or result.keypoints is None:
            logger.info("Detections: 0")
            return tracked_persons
            
        boxes = result.boxes
        keypoints = result.keypoints
        
        # Extract track IDs (ByteTrack)
        # Note: boxes.id might be None if tracking hasn't initialized or no detections exceed thresholds
        if boxes.id is not None:
            track_ids = boxes.id.int().cpu().tolist()
        else:
            track_ids = None

        # Iterate over all detections in the frame
        for i in range(len(boxes)):
            if track_ids is not None and i < len(track_ids):
                track_id = track_ids[i]
            else:
                track_id = None

            # Bounding box coordinates
            bbox = boxes.xyxy[i].cpu().numpy().tolist() # [x1, y1, x2, y2]
            box_conf = float(boxes.conf[i].cpu().item())
            
            # Keypoints (x, y coordinates and confidence)
            # keypoints.xy shape: (N, 17, 2), keypoints.conf shape: (N, 17)
            kp_xy = keypoints.xy[i].cpu().numpy() # Shape (17, 2)
            kp_conf = keypoints.conf[i].cpu().numpy() # Shape (17,)
            
            tracked_persons.append({
                "track_id": track_id,
                "bbox": bbox,
                "box_conf": box_conf,
                "keypoints": kp_xy,
                "keypoints_conf": kp_conf
            })
            
        logger.info(f"Detections: {len(tracked_persons)}")
        return tracked_persons
