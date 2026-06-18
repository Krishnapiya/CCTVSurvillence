import cv2
import threading
import time
import asyncio
from typing import Dict, Optional, List
import numpy as np
from uuid import UUID
from datetime import datetime, time as datetime_time
import pytz
from app.core.database import AsyncSessionLocal
from app.services.camera_manager import camera_manager
from app.services.video_manager import video_manager
from app.services.ai_engine import ai_engine
from app.core.config import settings

EVENT_TYPE_MAPPING = {
    "fire": "Fire Detection",
    "smoke": "Smoke Detection",
    "intrusion": "Human Detection",
    "mobile_usage": "Mobile Phone Detection",
    "bag": "Bag Detection",
    "bench": "Bench Detection"
}

active_job_ids_cache = set()
last_cache_update = 0.0
cache_lock = threading.Lock()

async def update_active_jobs_cache():
    global active_job_ids_cache, last_cache_update
    now = time.time()
    if now - last_cache_update < 5.0:
        return
        
    try:
        from app.repositories.alert_job import AlertJobRepository
        async with AsyncSessionLocal() as db_session:
            repo = AlertJobRepository(db_session)
            jobs = await repo.list(limit=1000)
            active_ids = {str(j.id) for j in jobs if j.is_active}
            global cache_lock
            with cache_lock:
                active_job_ids_cache = active_ids
                last_cache_update = now
    except Exception as e:
        print(f"Error updating active jobs cache: {e}")

def get_job_id_from_event(event_id: str) -> Optional[str]:
    if not event_id.startswith("E-"):
        return None
    parts = event_id.split("-")
    if len(parts) >= 7:
        return "-".join(parts[1:6])
    return None

def is_point_in_polygon(point, polygon) -> bool:
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

def is_schedule_active(event_rule: dict) -> bool:
    try:
        tz = pytz.timezone("Asia/Kolkata")
        now_local = datetime.now(tz)
        
        current_day = now_local.strftime("%A")
        rule_days = event_rule.get("days", [])
        if rule_days and "All Days" not in rule_days and current_day not in rule_days:
            return False
            
        start_str = event_rule.get("startTime", "00:00")
        end_str = event_rule.get("endTime", "23:59")
        
        start_h, start_m = map(int, start_str.split(":"))
        end_h, end_m = map(int, end_str.split(":"))
        
        now_time = now_local.time()
        start_time = datetime_time(start_h, start_m)
        end_time = datetime_time(end_h, end_m)
        
        if start_time <= end_time:
            return start_time <= now_time <= end_time
        else:
            return now_time >= start_time or now_time <= end_time
    except Exception as e:
        print(f"Error checking schedule activity: {e}")
        return False

def filter_events_by_schedules(events: list, rois: list, frame_shape: tuple, active_job_ids: set) -> list:
    if not rois:
        return []
        
    filtered = []
    h, w = frame_shape[:2]
    
    # Calculate scale factor from actual frame resolution to 800x450 canvas resolution
    scale_x = 800.0 / w if w > 0 else 1.0
    scale_y = 450.0 / h if h > 0 else 1.0
    
    for event in events:
        event_type = event.get("type")
        mapped_type = EVENT_TYPE_MAPPING.get(event_type)
        if not mapped_type:
            continue
            
        bbox = event.get("details", {}).get("bbox")
        if not bbox and "bbox1" in event.get("details", {}):
            bbox = event["details"]["bbox1"]
            
        if bbox:
            px = (bbox[0] + bbox[2]) // 2
            py = (bbox[1] + bbox[3]) // 2
        else:
            px = w // 2
            py = h // 2
            
        # Scale the point to the frontend canvas space (800x450)
        point = (int(px * scale_x), int(py * scale_y))
            
        matched_roi = None
        for roi in rois:
            points = roi.get("points", [])
            if points:
                poly = [(int(p["x"]), int(p["y"])) for p in points]
            elif "coords" in roi and roi["coords"]:
                coords = roi["coords"]
                left = coords.get("left", 0)
                top = coords.get("top", 0)
                width = coords.get("width", 0)
                height = coords.get("height", 0)
                poly = [
                    (int(left), int(top)),
                    (int(left + width), int(top)),
                    (int(left + width), int(top + height)),
                    (int(left), int(top + height))
                ]
            else:
                poly = []

            if is_point_in_polygon(point, poly):
                matched_roi = roi
                break
                
        if not matched_roi:
            continue
            
        roi_events = matched_roi.get("events", [])
        is_active = False
        for rule in roi_events:
            rule_id = rule.get("id", "")
            rule_job_id = get_job_id_from_event(rule_id)
            # Only process this rule if its job exists and is active!
            if not rule_job_id or rule_job_id not in active_job_ids:
                continue
                
            rule_type = rule.get("type", "")
            rule_types = [t.strip() for t in rule_type.split(",")]
            if mapped_type in rule_types:
                if is_schedule_active(rule):
                    is_active = True
                    break
                    
        if is_active:
            event["details"]["roi_name"] = matched_roi.get("name", "ROI")
            filtered.append(event)
            
    return filtered

class StreamProcessor(threading.Thread):
    def __init__(self, camera_id: str, rtsp_url: str, name: str, event_callback):
        super().__init__()
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.name = name
        self.event_callback = event_callback
        self.stopped = False
        self.daemon = True
        self.frame_count = 0
        self.fps = 0.0

    def run(self):
        print(f"Starting stream processor for camera {self.name} ({self.camera_id})")
        
        # Load ROIs from database
        self.rois = []
        from app.repositories.camera import CameraRepository
        async def load_rois():
            async with AsyncSessionLocal() as session:
                repo = CameraRepository(session)
                cam = await repo.get(UUID(self.camera_id))
                if cam:
                    return cam.rois
            return []
        
        try:
            if stream_processor_manager.loop:
                fut = asyncio.run_coroutine_threadsafe(load_rois(), stream_processor_manager.loop)
                self.rois = fut.result(timeout=3)
            print(f"Loaded {len(self.rois)} ROIs for camera {self.name}")
        except Exception as e:
            print(f"Failed to load ROIs for {self.name}: {e}")

        # Sync initial status
        self._sync_db_status("online")

        # RTSP reconnect loop
        while not self.stopped:
            # We support mocking files or testing with standard video loops
            cap = cv2.VideoCapture(self.rtsp_url)
            if not cap.isOpened():
                print(f"Failed to open RTSP stream for {self.name}. Retrying in 5s...")
                self._sync_db_status("offline")
                # Interruptible sleep
                for _ in range(50):
                    if self.stopped:
                        break
                    time.sleep(0.1)
                continue

            self._sync_db_status("online")
            last_fps_time = time.time()
            last_inference_time = time.time()
            frame_interval = 1.0 / 15.0  # Limit ingestion to 15 FPS

            while not self.stopped:
                loop_start = time.time()
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    print(f"Failed to retrieve frame from {self.name}. Reconnecting...")
                    self._sync_db_status("offline")
                    break

                self.frame_count += 1
                
                # Update ring buffer
                video_manager.add_frame(self.camera_id, frame)
                
                # Record post-trigger frames if there is an active session
                from app.services.event_engine import event_engine
                event_engine.check_and_record_post_trigger(self.camera_id, frame)

                # Calculate live FPS
                now = time.time()
                if now - last_fps_time >= 2.0:
                    self.fps = self.frame_count / (now - last_fps_time)
                    camera_manager.update_status(self.camera_id, "online", self.fps)
                    self.frame_count = 0
                    last_fps_time = now

                # Run inference periodically (e.g. 3 times per second to save CPU)
                if now - last_inference_time >= 0.33:
                    last_inference_time = now
                    # Run detection safely on the main thread's event loop
                    if stream_processor_manager.loop:
                        asyncio.run_coroutine_threadsafe(
                            self._run_detection(frame),
                            stream_processor_manager.loop
                        )

                # Rate limiting
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            cap.release()

        self._sync_db_status("offline")
        print(f"Stopped stream processor for camera {self.name}")

    async def _run_detection(self, frame: np.ndarray):
        try:
            # Parse configured ROIs into polygon points
            restricted_polygons = []
            if hasattr(self, "rois") and self.rois:
                for roi in self.rois:
                    if "points" in roi and roi["points"]:
                        poly = [(int(p["x"]), int(p["y"])) for p in roi["points"]]
                        restricted_polygons.append(poly)
                    elif "coords" in roi and roi["coords"]:
                        coords = roi["coords"]
                        left = coords.get("left", 0)
                        top = coords.get("top", 0)
                        width = coords.get("width", 0)
                        height = coords.get("height", 0)
                        poly = [
                            (int(left), int(top)),
                            (int(left + width), int(top)),
                            (int(left + width), int(top + height)),
                            (int(left), int(top + height))
                        ]
                        restricted_polygons.append(poly)

            # Run detection rules
            detected_events = await ai_engine.detect_frame(
                camera_id=self.camera_id,
                frame=frame,
                restricted_polygons=restricted_polygons
            )
            
            # Filter events based on active ROI schedules
            h, w, _ = frame.shape
            if hasattr(self, "rois") and self.rois:
                await update_active_jobs_cache()
                global active_job_ids_cache, cache_lock
                with cache_lock:
                    current_active_ids = set(active_job_ids_cache)
                detected_events = filter_events_by_schedules(detected_events, self.rois, (h, w), current_active_ids)
            else:
                detected_events = []

            for event in detected_events:
                # Trigger callback (which is asynchronous)
                await self.event_callback(self.camera_id, event, frame)
        except Exception as e:
            print(f"Error in stream detection for {self.name}: {e}")

    def _sync_db_status(self, status: str):
        # Update in-memory status instantly
        camera_manager.update_status(self.camera_id, status)

        # Run database persistence safely on the main event loop
        if stream_processor_manager.loop:
            async def sync():
                async with AsyncSessionLocal() as session:
                    await camera_manager.persist_status(self.camera_id, status, session)
                    await session.commit()
            
            asyncio.run_coroutine_threadsafe(sync(), stream_processor_manager.loop)

    def stop(self):
        self.stopped = True

class StreamProcessorManager:
    def __init__(self):
        # Maps camera_id -> StreamProcessor
        self.processors: Dict[str, StreamProcessor] = {}
        self.callback = None
        self.loop = None

    def set_callback(self, event_callback):
        self.callback = event_callback

    def start_camera_stream(self, camera_id: str, rtsp_url: str, name: str):
        if not self.callback:
            raise ValueError("Event callback must be set before starting streams.")

        self.stop_camera_stream(camera_id)
        
        processor = StreamProcessor(camera_id, rtsp_url, name, self.callback)
        processor.start()
        self.processors[camera_id] = processor

    def stop_camera_stream(self, camera_id: str):
        if camera_id in self.processors:
            processor = self.processors[camera_id]
            processor.stop()
            processor.join(timeout=0.2)
            del self.processors[camera_id]

    def stop_all(self):
        for processor in list(self.processors.values()):
            processor.stop()
        for camera_id in list(self.processors.keys()):
            self.stop_camera_stream(camera_id)

stream_processor_manager = StreamProcessorManager()
