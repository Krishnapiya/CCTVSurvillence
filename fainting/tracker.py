import logging
import time
import numpy as np
from detector import PoseDetector

logger = logging.getLogger("fall_detection.tracker")

def calculate_iou(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x1_i >= x2_i or y1_i >= y2_i:
        return 0.0
        
    area_i = (x2_i - x1_i) * (y2_i - y1_i)
    area_box1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area_box2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    area_u = area_box1 + area_box2 - area_i
    
    return area_i / max(1.0, area_u)

class PersonTracker:
    def __init__(self):
        """
        Initialize the tracker manager, which uses PoseDetector to detect and track people.
        """
        self.detector = PoseDetector()
        self.active_tracks = set()
        self.tracks_cache = {}
        self.next_fallback_id = 1000

    def update(self, frame: np.ndarray) -> list:
        """
        Tracks people in the new frame and updates the set of active IDs.
        
        Args:
            frame: OpenCV image frame (BGR).
            
        Returns:
            A list of tracked person dictionaries.
        """
        persons = self.detector.detect_and_track(frame)
        current_time = time.time()
        
        # Clean up cache: remove tracks not seen for > 5.0 seconds
        self.tracks_cache = {
            tid: info for tid, info in self.tracks_cache.items()
            if (current_time - info["last_seen"]) <= 5.0
        }
        
        matched_prev_ids = set()
        
        # First, try to match by reusing the same track ID if it matches the cache well
        for p in persons:
            p_id = p.get("track_id")
            if p_id is not None:
                # Find if this ID is in cache and overlaps well
                cached = self.tracks_cache.get(p_id)
                if cached:
                    iou = calculate_iou(p["bbox"], cached["bbox"])
                    if iou > 0.30:
                        matched_prev_ids.add(p_id)
                        continue
                
                # If no match in cache, clear the ID to match it by IOU
                p["track_id"] = None
        
        # Now, for all unmatched persons, match to cache by IOU
        for p in persons:
            if p.get("track_id") is None:
                best_match_id = None
                best_iou = 0.0
                bbox = p["bbox"]
                
                for tid, cached in self.tracks_cache.items():
                    if tid in matched_prev_ids:
                        continue
                        
                    iou = calculate_iou(bbox, cached["bbox"])
                    if iou > 0.20 and iou > best_iou:
                        best_iou = iou
                        best_match_id = tid
                
                if best_match_id is not None:
                    p["track_id"] = best_match_id
                    matched_prev_ids.add(best_match_id)
                else:
                    p["track_id"] = self.next_fallback_id
                    self.next_fallback_id += 1
        
        # Update cache with the new positions
        for p in persons:
            tid = p["track_id"]
            self.tracks_cache[tid] = {
                "bbox": p["bbox"],
                "last_seen": current_time
            }
            
        # Keep track of currently visible IDs
        current_ids = {p["track_id"] for p in persons}
        
        # Log when new tracks appear or old tracks disappear
        new_tracks = current_ids - self.active_tracks
        lost_tracks = self.active_tracks - current_ids
        
        if new_tracks:
            logger.info(f"New person(s) tracked: {new_tracks}")
        if lost_tracks:
            logger.info(f"Person(s) lost from tracking: {lost_tracks}")
            
        self.active_tracks = current_ids
        
        return persons

    def get_active_ids(self) -> set:
        """
        Returns the set of currently active (visible) track IDs.
        """
        return self.active_tracks
