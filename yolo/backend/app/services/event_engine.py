import os
import cv2
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.event import Event, Snapshot
from app.models.alert import Alert
from app.repositories.event import EventRepository, SnapshotRepository
from app.repositories.alert import AlertRepository
from app.services.video_manager import video_manager
from app.services.websocket_manager import ws_manager

class EventEngine:
    def __init__(self):
        # Cooldown manager to prevent duplicate event spam
        self.cooldowns: Dict[Tuple[str, str], float] = {}
        self.cooldown_duration = 30.0
        
        # Active recording sessions for post-trigger capturing
        # Maps event_id (str) -> {"camera_id": str, "temp_dir": str, "frames_written": int, "max_frames": int}
        self.active_recordings: Dict[str, Dict[str, Any]] = {}

    def _determine_severity(self, event_type: str) -> str:
        high_critical = ["fire", "suicide_risk", "fight", "intrusion", "human_detection"]
        medium = ["fainting", "projectile", "smoke"]
        if event_type in high_critical:
            return "CRITICAL"
        elif event_type in medium:
            return "HIGH"
        return "MEDIUM"

    def check_and_record_post_trigger(self, camera_id: str, frame: np.ndarray):
        """
        Called by the RTSP stream processor for every frame captured.
        Saves frames if there is an active post-trigger recording session.
        """
        finished_events = []
        for event_id, session in list(self.active_recordings.items()):
            if session["camera_id"] == camera_id:
                idx = session["frames_written"]
                temp_dir = session["temp_dir"]
                
                # Save frame
                frame_path = os.path.join(temp_dir, f"frame_post_{idx:05d}_{time.time()}.jpg")
                try:
                    cv2.imwrite(frame_path, frame)
                    session["frames_written"] += 1
                except Exception as e:
                    print(f"Error writing post-trigger frame: {e}")

                # Check if session finished (5 seconds @ 15fps = 75 frames)
                if session["frames_written"] >= session["max_frames"]:
                    # Write sentinel file
                    sentinel_path = os.path.join(temp_dir, "complete.txt")
                    with open(sentinel_path, "w") as f:
                        f.write("done")
                    finished_events.append(event_id)

        for event_id in finished_events:
            if event_id in self.active_recordings:
                del self.active_recordings[event_id]

    async def handle_detection(self, camera_id: str, detection: Dict[str, Any], frame: np.ndarray):
        event_type = detection["type"]
        confidence = detection["confidence"]
        roi_name = detection.get("details", {}).get("roi_name")
        if roi_name is not None:
            roi_name = str(roi_name).strip() or None
        
        # Apply cooldown check
        now = time.time()
        key = (camera_id, event_type)
        if key in self.cooldowns:
            if now - self.cooldowns[key] < self.cooldown_duration:
                return
                
        self.cooldowns[key] = now
        event_id = uuid.uuid4()
        
        # 1. Save Snapshot immediately
        snapshot_filename = f"{event_id}.jpg"
        snapshot_dir = os.path.join(settings.MEDIA_STORAGE_DIR, "snapshots")
        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
        
        try:
            cv2.imwrite(snapshot_path, frame)
        except Exception as e:
            print(f"Failed to write snapshot image: {e}")
            snapshot_path = ""

        # 2. Save Pre-trigger frames (5s buffer)
        temp_frames_dir = video_manager.save_pre_trigger_frames(camera_id, str(event_id))

        if temp_frames_dir:
            # Register post-trigger session to capture the next 5 seconds
            fps_target = 15
            max_frames = int(settings.POST_TRIGGER_DURATION_SECS * fps_target)
            self.active_recordings[str(event_id)] = {
                "camera_id": camera_id,
                "temp_dir": temp_frames_dir,
                "frames_written": 0,
                "max_frames": max_frames
            }

        # 3. Persist to PostgreSQL database
        async with AsyncSessionLocal() as db:
            event_repo = EventRepository(db)
            snapshot_repo = SnapshotRepository(db)
            alert_repo = AlertRepository(db)

            # Create Event entry
            db_event = await event_repo.create({
                "id": event_id,
                "camera_id": uuid.UUID(camera_id),
                "type": event_type,
                "confidence": confidence,
                "roi_name": roi_name,
                "snapshot_path": snapshot_path,
                "video_clip_path": "",
                "timestamp": datetime.now(timezone.utc)
            })

            # Create Snapshot entry
            h, w, _ = frame.shape
            await snapshot_repo.create({
                "event_id": event_id,
                "file_path": snapshot_path,
                "resolution": f"{w}x{h}"
            })

            # Create Alert entry
            severity = self._determine_severity(event_type)
            db_alert = await alert_repo.create({
                "event_id": event_id,
                "status": "CREATED",
                "severity": severity
            })

            await db.commit()

        # 4. Broadcast via WebSocket
        ws_payload = {
            "msg_type": "new_alert",
            "alert": {
                "id": str(db_alert.id),
                "event_id": str(event_id),
                "camera_id": camera_id,
                "type": event_type,
                "confidence": confidence,
                "severity": severity,
                "roi_name": roi_name,
                "status": "CREATED",
                "snapshot_url": f"/media/snapshots/{snapshot_filename}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        await ws_manager.broadcast(ws_payload)

        # 5. Dispatch background task (Celery) or run in a local background thread if Celery is offline
        from app.workers.tasks import process_event_clip_and_verify
        try:
            process_event_clip_and_verify.delay(
                event_id=str(event_id),
                camera_id=camera_id,
                temp_frames_dir=temp_frames_dir,
                event_type=event_type,
                snapshot_path=snapshot_path
            )
            print("Successfully dispatched event verification task via Celery.")
        except Exception as celery_err:
            print(f"Celery operational error: {celery_err}. Falling back to local background thread execution.")
            import threading
            def run_in_background():
                try:
                    process_event_clip_and_verify(
                        event_id=str(event_id),
                        camera_id=camera_id,
                        temp_frames_dir=temp_frames_dir,
                        event_type=event_type,
                        snapshot_path=snapshot_path
                    )
                except Exception as e:
                    print(f"Error running local clip & verify task: {e}")
            threading.Thread(target=run_in_background, daemon=True).start()

# Global Instance
event_engine = EventEngine()
# The callback registration is handled inside the stream manager init or setup
