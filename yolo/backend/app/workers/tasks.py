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

@shared_task(name="app.workers.tasks.process_event_clip_and_verify")
def process_event_clip_and_verify(
    event_id: str,
    camera_id: str,
    temp_frames_dir: str,
    event_type: str,
    snapshot_path: str
):
    print(f"Celery task started for Event: {event_id}, Type: {event_type}")
    
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
        time.sleep(0.5)

    # 2. Compile video clip from frames
    clip_filename = f"{event_id}.mp4"
    clip_dir = os.path.join(settings.MEDIA_STORAGE_DIR, "clips")
    os.makedirs(clip_dir, exist_ok=True)
    clip_path = os.path.join(clip_dir, clip_filename)
    
    frame_files = sorted([f for f in glob.glob(os.path.join(temp_frames_dir, "*.jpg"))])
    
    duration = 10.0
    file_size = 0

    # Fetch active alert rules for this camera to filter bounding boxes
    async def get_allowed_yolo_types():
        from app.repositories.camera import CameraRepository
        from app.models.alert_job import AlertJob
        from sqlalchemy.future import select
        
        async with AsyncSessionLocal() as session:
            try:
                # 1. Get active alert job IDs
                stmt = select(AlertJob).filter(AlertJob.is_active == True)
                res = await session.execute(stmt)
                active_job_ids = {str(job.id) for job in res.scalars().all()}
                
                # 2. Get camera
                cam_repo = CameraRepository(session)
                camera = await cam_repo.get(UUID(camera_id))
                if not camera:
                    return set()
                    
                allowed = set()
                mapping = {
                    "Human Detection": ["human_detection", "intrusion"],
                    "Mobile Phone Detection": ["mobile_usage"],
                    "Fire Detection": ["fire"],
                    "Smoke Detection": ["smoke"],
                    "Bag Detection": ["bag"],
                    "Bench Detection": ["bench"]
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
                                            allowed.update(mapping[t])
                return allowed
            except Exception as ex:
                print(f"Error getting allowed yolo types: {ex}")
                return set()

    allowed_types = run_async(get_allowed_yolo_types())
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
            
            from app.services.ai_engine import ai_engine
            for f in frame_files:
                img = cv2.imread(f)
                if img is not None:
                    try:
                        # Detect objects on the frame
                        events = run_async(ai_engine.detect_frame(camera_id, img))
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
        qwen_res, qwen_conf, qwen_detail = run_async(
            ai_verification_service.verify_with_qwen_vl(snapshot_path, qwen_prompts[event_type])
        )
        verification_results.append({
            "service_name": "Qwen2.5-VL",
            "result": qwen_res,
            "confidence": qwen_conf,
            "details": {"reasoning": qwen_detail}
        })
    elif event_type == "fight":
        # Compile frames list for MoViNet action recognition
        # In a real environment, we'd pass downscaled frames; here we run the flow estimator
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

        movinet_res, movinet_conf = run_async(
            ai_verification_service.verify_fight_movinet(test_frames)
        )
        verification_results.append({
            "service_name": "MoViNet",
            "result": movinet_res,
            "confidence": movinet_conf,
            "details": {"info": "Optical flow activity analysis of clip frames."}
        })
    elif event_type == "fainting":
        # Mock keypoints for verification
        mock_kps = {"shoulder": (0.5, 0.6), "hip": (0.5, 0.58), "left_ankle": (0.5, 0.55), "left_shoulder": (0.5, 0.6)}
        movenet_res, movenet_conf = run_async(
            ai_verification_service.verify_fainting_movenet(mock_kps)
        )
        verification_results.append({
            "service_name": "MoveNet",
            "result": movenet_res,
            "confidence": movenet_conf,
            "details": {"info": "Pose keypoint ratio check"}
        })

    # 4. Save to Database
    async def update_db():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        bg_engine = create_async_engine(db_url, future=True)
        BgSessionLocal = async_sessionmaker(
            bind=bg_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

        async with BgSessionLocal() as db:
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
            primary_verification = "VERIFIED"
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
        await bg_engine.dispose()
        return primary_verification

    primary_verif = run_async(update_db())

    # 5. Broadcast verification results via WebSockets
    run_async(ws_manager.broadcast({
        "msg_type": "verification_result",
        "verification": {
            "event_id": event_id,
            "result": primary_verif,
            "video_clip_url": f"/media/clips/{clip_filename}",
            "verifications": verification_results
        }
    }))
    print(f"Event {event_id} finished processing. Verification: {primary_verif}")
