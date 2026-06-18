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
                    elif label == "cell phone" and conf >= 0.5:
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

        return events

ai_engine = AIEngine()
