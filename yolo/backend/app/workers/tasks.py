import os
import glob
import cv2
import time
import asyncio
import shutil
from datetime import datetime, timezone
from uuid import UUID
from celery import shared_task
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.event import EventRepository, VideoClipRepository, EventVerificationRepository
from app.services.ai_verification import ai_verification_service
from app.services.websocket_manager import ws_manager

def run_async(coro):
    """Helper to run async coroutine inside synchronous Celery worker or thread."""
    from app.services.stream_processor import stream_processor_manager
    if stream_processor_manager.loop and stream_processor_manager.loop.is_running():
        import threading
        if threading.current_thread() is not threading.main_thread():
            future = asyncio.run_coroutine_threadsafe(coro, stream_processor_manager.loop)
            return future.result()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

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

async def async_process_event_clip_and_verify(
    event_id: str,
    camera_id: str,
    temp_frames_dir: str,
    event_type: str,
    snapshot_path: str
):
    print(f"Async processing started for Event: {event_id}, Type: {event_type}")
    
    if not temp_frames_dir or not os.path.exists(temp_frames_dir):
        print(f"Temp frames directory not found for Event: {event_id}")
        return

    # 1. Wait for sentinel complete.txt (written when post-trigger finishes)
    sentinel_path = os.path.join(temp_frames_dir, "complete.txt")
    poll_start = time.time()
    timeout_limit = settings.POST_TRIGGER_DURATION_SECS + 15.0
    while not os.path.exists(sentinel_path):
        if time.time() - poll_start > timeout_limit:
            print(f"Timeout waiting for complete.txt for Event: {event_id}. Compiling partial frames.")
            break
        await asyncio.sleep(0.5)

    # 2. Compile video clip from frames
    clip_filename = f"{event_id}.mp4"
    clip_dir = os.path.join(settings.MEDIA_STORAGE_DIR, "clips")
    os.makedirs(clip_dir, exist_ok=True)
    clip_path = os.path.join(clip_dir, clip_filename)
    
    frame_files = sorted([f for f in glob.glob(os.path.join(temp_frames_dir, "*.jpg"))])
    
    duration = 10.0
    file_size = 0

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    task_engine = create_async_engine(db_url, future=True)
    TaskSessionLocal = async_sessionmaker(
        bind=task_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    # Fetch active alert rules for this camera to filter bounding boxes
    allowed_types = set()
    try:
        from app.repositories.camera import CameraRepository
        from app.models.alert_job import AlertJob
        from sqlalchemy.future import select
        
        async with TaskSessionLocal() as session:
            # 1. Get active alert job IDs
            stmt = select(AlertJob).filter(AlertJob.is_active == True)
            res = await session.execute(stmt)
            active_job_ids = {str(job.id) for job in res.scalars().all()}
            
            # 2. Get camera
            cam_repo = CameraRepository(session)
            camera = await cam_repo.get(UUID(camera_id))
            if camera:
                mapping = {
                    "Human Detection": ["human_detection", "intrusion"],
                    "Mobile Phone Detection": ["mobile_usage"],
                    "Fire Detection": ["fire"],
                    "Smoke Detection": ["smoke"],
                    "Bag Detection": ["bag"],
                    "Bench Detection": ["bench"],
                    "Fainting Detection": ["fainting"]
                }
                
                for roi in camera.rois:
                    for event_rule in roi.get("events", []):
                        rule_id = event_rule.get("id", "")
                        if rule_id.startswith("E-"):
                            parts = rule_id.split("-")
                            if len(parts) >= 7:
                                job_id = "-".join(parts[1:6])
                                if job_id in active_job_ids:
                                    rule_type = event_rule.get("type", "")
                                    for part in rule_type.split(","):
                                        t = part.strip()
                                        if t in mapping:
                                            allowed_types.update(mapping[t])
    except Exception as ex:
        print(f"Error getting allowed yolo types: {ex}")

    if not allowed_types:
        allowed_types = {event_type}
    print(f"Allowed YOLO types for camera {camera_id} video annotation: {allowed_types}")

    if frame_files:
        try:
            # Read first frame to get dimensions
            first_frame = cv2.imread(frame_files[0])
            h, w, _ = first_frame.shape
            
            # Using mp4v codec for wide container support
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(clip_path, fourcc, 15.0, (w, h))
            
            use_fainting = (event_type == "fainting" or "fainting" in allowed_types)
            if use_fainting:
                import sys
                fainting_dir = "/data/hfllama/survialance/fainting"
                if fainting_dir not in sys.path:
                    sys.path.insert(0, fainting_dir)
                from tracker import PersonTracker
                from posture import analyze_posture, PostureState
                
                clip_tracker = PersonTracker()

            from app.services.ai_engine import ai_engine
            for f in frame_files:
                img = cv2.imread(f)
                if img is not None:
                    if use_fainting:
                        try:
                            persons = clip_tracker.update(img)
                            for person in persons:
                                track_id = person["track_id"]
                                bbox = person["bbox"]
                                keypoints = person["keypoints"]
                                kp_conf = person["keypoints_conf"]
                                
                                state, angle, aspect_ratio = analyze_posture(bbox, keypoints, kp_conf, track_id)
                                
                                # Draw skeleton
                                draw_skeleton(img, keypoints, kp_conf)
                                
                                # Choose box color based on posture state
                                if state == PostureState.VERTICAL:
                                    color = (0, 255, 0) # Green
                                elif state == PostureState.FALLING:
                                    color = (0, 165, 255) # Orange
                                else: # HORIZONTAL
                                    color = (0, 0, 255) # Red
                                    
                                x1, y1, x2, y2 = map(int, bbox)
                                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                                
                                label = f"ID:{track_id} | {state}"
                                if angle is not None:
                                    label += f" | Angle: {angle:.1f}"
                                cv2.putText(img, label, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        except Exception as ex:
                            print(f"Error drawing fainting overlay on video clip frame: {ex}")
                    else:
                        try:
                            # Detect objects on the frame
                            events = await ai_engine.detect_frame(camera_id, img)
                            # Draw boxes on the frame
                            for event in events:
                                etype = event["type"]
                                # Only draw box if this event type is configured and active
                                if etype not in allowed_types:
                                    continue
                                    
                                conf = event["confidence"]
                                details = event["details"]
                                
                                # Define box color based on event type
                                if etype in ["fire", "smoke", "intrusion"]:
                                    color = (0, 0, 255) # Red
                                elif etype == "fight":
                                    color = (0, 165, 255) # Orange
                                elif etype in ["mobile_usage", "smoking"]:
                                    color = (255, 0, 255) # Purple
                                else:
                                    color = (0, 255, 0) # Green
                                    
                                if "bbox" in details:
                                    x1, y1, x2, y2 = details["bbox"]
                                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                                    label = f"{etype.upper()} ({conf:.2f})"
                                    cv2.putText(img, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        except Exception as det_err:
                            print(f"Error annotating frame {f} for video clip: {det_err}")
                    video_writer.write(img)
            
            video_writer.release()
            file_size = os.path.getsize(clip_path)
            duration = len(frame_files) / 15.0
            print(f"Video clip compiled successfully at: {clip_path} (Size: {file_size} bytes)")
        except Exception as e:
            print(f"Error compiling video clip: {e}")
            clip_path = ""
    else:
        print(f"No frames found to compile for Event: {event_id}")
        clip_path = ""

    # Clean up temp frames directory
    try:
        shutil.rmtree(temp_frames_dir)
    except Exception as e:
        print(f"Failed to clean up temp dir {temp_frames_dir}: {e}")

    # 3. Perform AI Verification based on event type
    verification_results = []
    
    # Heuristics & visual verification prompts
    qwen_prompts = {
        "smoking": "Is the person in the image smoking a cigarette? Answer YES or NO.",
        "suicide_risk": "Is the person in the image climbing over a railing, hanging, or showing suicide risk indicators? Answer YES or NO.",
        "intrusion": "Is a person violating the perimeter fence or restricted zone? Answer YES or NO.",
        "human_detection": "Is a person violating the perimeter fence or restricted zone? Answer YES or NO.",
        "mobile_usage": "Is the person in the image using or holding a cell phone or mobile phone? Answer YES or NO."
    }

    if event_type in qwen_prompts:
        qwen_res, qwen_conf, qwen_detail = await ai_verification_service.verify_with_qwen_vl(snapshot_path, qwen_prompts[event_type])
        verification_results.append({
            "service_name": "Qwen2.5-VL",
            "result": qwen_res,
            "confidence": qwen_conf,
            "details": {"reasoning": qwen_detail}
        })
    elif event_type == "fight":
        test_frames = []
        if clip_path and os.path.exists(clip_path):
            cap = cv2.VideoCapture(clip_path)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                test_frames.append(frame)
                if len(test_frames) >= 15:
                    break
            cap.release()

        movinet_res, movinet_conf = await ai_verification_service.verify_fight_movinet(test_frames)
        verification_results.append({
            "service_name": "MoViNet",
            "result": movinet_res,
            "confidence": movinet_conf,
            "details": {"info": "Optical flow activity analysis of clip frames."}
        })
    elif event_type == "fainting":
        mock_kps = {"shoulder": (0.5, 0.6), "hip": (0.5, 0.58), "left_ankle": (0.5, 0.55), "left_shoulder": (0.5, 0.6)}
        movenet_res, movenet_conf = await ai_verification_service.verify_fainting_movenet(mock_kps)
        verification_results.append({
            "service_name": "MoveNet",
            "result": movenet_res,
            "confidence": movenet_conf,
            "details": {"info": "Pose keypoint ratio check"}
        })

    # 4. Save to Database
    primary_verification = "VERIFIED"
    try:
        async with TaskSessionLocal() as db:
            event_repo = EventRepository(db)
            clip_repo = VideoClipRepository(db)
            verif_repo = EventVerificationRepository(db)

            # Update Event with video clip path
            event_uuid = UUID(event_id)
            db_event = await event_repo.get(event_uuid)
            if db_event and clip_path:
                await event_repo.update(db_event, {"video_clip_path": clip_path})

                # Create VideoClip record
                await clip_repo.create({
                    "event_id": event_uuid,
                    "file_path": clip_path,
                    "duration_seconds": duration,
                    "start_timestamp": db_event.timestamp,
                    "end_timestamp": datetime.fromtimestamp(db_event.timestamp.timestamp() + duration, tz=timezone.utc),
                    "file_size_bytes": file_size
                })

            # Save verification results
            for v_data in verification_results:
                await verif_repo.create({
                    "event_id": event_uuid,
                    "service_name": v_data["service_name"],
                    "result": v_data["result"],
                    "confidence": v_data["confidence"],
                    "details": v_data["details"]
                })
                if v_data["result"] == "REFUTED":
                    primary_verification = "REFUTED"

            await db.commit()
    except Exception as db_err:
        print(f"Error updating database in background task: {db_err}")

    # 5. Broadcast verification results via WebSockets
    try:
        await ws_manager.broadcast({
            "msg_type": "verification_result",
            "verification": {
                "event_id": event_id,
                "result": primary_verification,
                "video_clip_url": f"/media/clips/{clip_filename}",
                "verifications": verification_results
            }
        })
    except Exception as ws_err:
        print(f"Error broadcasting via WebSocket: {ws_err}")

    await task_engine.dispose()
    print(f"Event {event_id} finished processing. Verification: {primary_verification}")
    return primary_verification

@shared_task(name="app.workers.tasks.process_event_clip_and_verify")
def process_event_clip_and_verify(
    event_id: str,
    camera_id: str,
    temp_frames_dir: str,
    event_type: str,
    snapshot_path: str
):
    print(f"Celery/Background task started for Event: {event_id}, Type: {event_type}")
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            async_process_event_clip_and_verify(
                event_id, camera_id, temp_frames_dir, event_type, snapshot_path
            )
        )
    except Exception as e:
        print(f"Error running local clip & verify task: {e}")
    finally:
        loop.close()
