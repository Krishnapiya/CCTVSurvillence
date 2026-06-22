import cv2
import numpy as np
import os
import torch
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO
from app.core.config import settings

class AIEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._fire_model = None
        self._general_model = None
        self._pose_model = None

    def _init_models(self):
        """Lazy load models when first stream frame arrives to prevent import blocks."""
        if self._fire_model is None:
            custom_path = settings.YOLO_CUSTOM_FIRE_SMOKE_PATH
            if not os.path.exists(custom_path):
                raise FileNotFoundError(f"Custom weights not found at {custom_path}. Custom fire/smoke model is required.")
            self._fire_model = YOLO(custom_path)
            self._fire_model.to(self.device)

        if self._general_model is None:
            self._general_model = YOLO(settings.YOLO_PRETRAINED_DETECTION_PATH)
            self._general_model.to(self.device)

        if self._pose_model is None:
            self._pose_model = YOLO("yolo11s-pose.pt")
            self._pose_model.to(self.device)

    def _is_point_in_polygon(self, point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
        if not polygon or len(polygon) < 3:
            return False
        x, y = point
        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    async def detect_frame(
        self, 
        camera_id: str, 
        frame: np.ndarray, 
        restricted_polygons: List[List[Tuple[int, int]]] = None,
        reference_uniforms: List[np.ndarray] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs custom fire/smoke model and general YOLOv11 model on the frame.
        Returns a list of generated event payloads matching active features.
        """
        self._init_models()
        events = []
        
        # --- 1. RUN CUSTOM FIRE & SMOKE YOLO ---
        try:
            fire_res = self._fire_model(frame, verbose=False)
            for r in fire_res:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = self._fire_model.names[cls_id].lower()
                    conf = float(box.conf[0])
                    
                    if conf >= 0.45:
                        if label in ["fire", "smoke"]:
                            events.append({
                                "type": label,
                                "confidence": conf,
                                "details": {"bbox": [int(x) for x in box.xyxy[0].tolist()]}
                            })
        except Exception as e:
            print(f"Error running custom fire/smoke model: {e}")

        # --- 2. RUN GENERAL PRETRAINED YOLOv11 ---
        try:
            general_res = self._general_model(frame, verbose=False)
            for r in general_res:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = self._general_model.names[cls_id].lower()
                    conf = float(box.conf[0])
                    bbox = [int(x) for x in box.xyxy[0].tolist()]

                    # Person detection (human_detection)
                    if label == "person" and conf >= 0.5:
                        events.append({
                            "type": "human_detection",
                            "confidence": conf,
                            "details": {"bbox": bbox}
                        })
                    
                    # Mobile phone detection
                    elif label == "cell phone" and conf >= 0.25:
                        events.append({
                            "type": "mobile_usage",
                            "confidence": conf,
                            "details": {"bbox": bbox}
                        })

                    # Bag detection (backpack, handbag, suitcase)
                    elif label in ["backpack", "handbag", "suitcase"] and conf >= 0.45:
                        events.append({
                            "type": "bag",
                            "confidence": conf,
                            "details": {"bbox": bbox}
                        })

                    # Bench detection
                    elif label == "bench" and conf >= 0.45:
                        events.append({
                            "type": "bench",
                            "confidence": conf,
                            "details": {"bbox": bbox}
                        })
        except Exception as e:
            print(f"Error running general pretrained model: {e}")

        # --- 3. RUN YOLO POSE FOR FIGHT DETECTION ---
        try:
            pose_res = self._pose_model(frame, verbose=False)
            if pose_res and len(pose_res) > 0 and pose_res[0].keypoints is not None:
                keypoints_data = pose_res[0].keypoints.xy.cpu().numpy()
                keypoints_conf = pose_res[0].keypoints.conf.cpu().numpy() if pose_res[0].keypoints.conf is not None else None
                boxes_data = pose_res[0].boxes.xyxy.cpu().numpy()
                box_confs = pose_res[0].boxes.conf.cpu().numpy() if pose_res[0].boxes.conf is not None else None
                
                # Filter for people within the restricted polygons with high confidence (>0.55)
                active_kps = []
                active_boxes = []
                active_confs = []
                
                for idx, box in enumerate(boxes_data):
                    # Filter out low-confidence/ghost detections
                    if box_confs is not None and box_confs[idx] < 0.55:
                        continue
                        
                    px = int((box[0] + box[2]) / 2)
                    py = int((box[1] + box[3]) / 2)
                    
                    # If inside restricted polygon (ROI)
                    in_roi = False
                    if not restricted_polygons:
                        in_roi = True
                    else:
                        for poly in restricted_polygons:
                            if self._is_point_in_polygon((px, py), poly):
                                in_roi = True
                                break
                                
                    if in_roi:
                        active_kps.append(keypoints_data[idx])
                        active_boxes.append(box)
                        if keypoints_conf is not None:
                            active_confs.append(keypoints_conf[idx])
                        else:
                            active_confs.append(np.ones(len(keypoints_data[idx])))
                            
                fight_events = self._detect_fight_from_poses(active_kps, active_boxes, active_confs)
                events.extend(fight_events)
        except Exception as e:
            print(f"Error running pose/fight detection model: {e}")

        return events

    def _detect_fight_from_poses(self, keypoints_list: list, bboxes_list: list, confs_list: list) -> List[Dict[str, Any]]:
        """
        Detect fights between pairs of people based on YOLO Pose keypoints.
        Includes advanced heuristics (IoU, center distance, hand-to-body distance)
        to prevent false detections from single persons or double-detections.
        """
        events = []
        n = len(keypoints_list)
        if n < 2:
            return events

        def get_iou(box1, box2):
            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])
            
            intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
            area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
            union = area1 + area2 - intersection
            if union <= 0.0:
                return 0.0
            return intersection / union

        for i in range(n):
            for j in range(i + 1, n):
                kps_a = keypoints_list[i]
                kps_b = keypoints_list[j]
                box_a = bboxes_list[i]
                box_b = bboxes_list[j]
                conf_a = confs_list[i]
                conf_b = confs_list[j]

                # 1. Double-detection Filter:
                # If two bounding boxes are almost overlapping (high IoU), it's likely a double-detection of the same person.
                if get_iou(box_a, box_b) > 0.65:
                    continue

                # 2. Proximity check based on box center distance relative to height
                center_a = ((box_a[0] + box_a[2]) / 2, (box_a[1] + box_a[3]) / 2)
                center_b = ((box_b[0] + box_b[2]) / 2, (box_b[1] + box_b[3]) / 2)
                center_dist = np.linalg.norm(np.array(center_a) - np.array(center_b))
                avg_height = ((box_a[3] - box_a[1]) + (box_b[3] - box_b[1])) / 2
                
                # If center distance is too small, they are likely the same person or standing in the exact same spot.
                if center_dist < 0.15 * avg_height:
                    continue
                    
                # If they are too far apart (cannot physically touch/reach), they cannot be fighting.
                if center_dist > 1.35 * avg_height:
                    continue

                # 3. Contact Interaction Heuristics:
                # Measure distance from wrists (indices 9, 10) to the other person's upper body/torso/head (0 to 6, 11, 12).
                min_dist = float('inf')
                
                # Check A's wrists to B's body
                for wrist_idx in [9, 10]:
                    if conf_a[wrist_idx] > 0.35:
                        wrist_pt = kps_a[wrist_idx]
                        for body_idx in [0, 1, 2, 3, 4, 5, 6, 11, 12]:
                            if conf_b[body_idx] > 0.35:
                                body_pt = kps_b[body_idx]
                                dist = np.linalg.norm(wrist_pt - body_pt)
                                if dist < min_dist:
                                    min_dist = dist
                                    
                # Check B's wrists to A's body
                for wrist_idx in [9, 10]:
                    if conf_b[wrist_idx] > 0.35:
                        wrist_pt = kps_b[wrist_idx]
                        for body_idx in [0, 1, 2, 3, 4, 5, 6, 11, 12]:
                            if conf_a[body_idx] > 0.35:
                                body_pt = kps_a[body_idx]
                                dist = np.linalg.norm(wrist_pt - body_pt)
                                if dist < min_dist:
                                    min_dist = dist

                # If minimum distance is within strike range (e.g. 18% of avg height)
                if min_dist < 0.18 * avg_height:
                    proximity_score = max(0.0, 1.0 - (min_dist / (0.25 * avg_height)))
                    confidence = 0.55 + 0.45 * proximity_score
                    
                    events.append({
                        "type": "fight",
                        "confidence": float(confidence),
                        "details": {
                            "bbox1": [int(x) for x in box_a],
                            "bbox2": [int(x) for x in box_b],
                            "distance_ratio": float(min_dist / avg_height)
                        }
                    })
                    
        return events

ai_engine = AIEngine()
