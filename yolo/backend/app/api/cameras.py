from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.camera import CameraRepository, CameraGroupRepository
from app.schemas.camera import CameraResponse, CameraCreate, CameraUpdate, CameraGroupResponse, CameraGroupCreate, CameraStatusResponse
from app.api import deps
from app.models.user import User
from app.services.stream_processor import stream_processor_manager
from app.services.camera_manager import camera_manager

router = APIRouter()

# --- CAMERA GROUPS ---

@router.get("/groups", response_model=List[CameraGroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = CameraGroupRepository(db)
    return await repo.list()

@router.post("/groups", response_model=CameraGroupResponse)
async def create_group(
    *,
    db: AsyncSession = Depends(get_db),
    group_in: CameraGroupCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = CameraGroupRepository(db)
    existing = await repo.get_by_name(group_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Group with this name already exists.")
    
    group = await repo.create(group_in.dict())
    await db.commit()
    return group

# --- CAMERAS ---

@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = CameraRepository(db)
    cameras = await repo.list()
    
    # Overlay real-time in-memory status
    for c in cameras:
        live = camera_manager.get_live_status(str(c.id))
        c.status = live["status"]
        
    return cameras

@router.post("", response_model=CameraResponse)
async def create_camera(
    *,
    db: AsyncSession = Depends(get_db),
    camera_in: CameraCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = CameraRepository(db)
    existing = await repo.get_by_name(camera_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Camera with this name already exists.")

    camera = await repo.create(camera_in.dict())
    await db.commit()

    # Dynamically spin up the RTSP thread
    try:
        stream_processor_manager.start_camera_stream(
            camera_id=str(camera.id),
            rtsp_url=camera.rtsp_url,
            name=camera.name
        )
    except Exception as e:
        print(f"Failed to start camera thread dynamically: {e}")

    return camera

@router.put("/{id}", response_model=CameraResponse)
async def update_camera(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    camera_in: CameraUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = CameraRepository(db)
    camera = await repo.get(id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")

    old_url = camera.rtsp_url
    updated_camera = await repo.update(camera, camera_in.dict(exclude_unset=True))
    await db.commit()

    # Dynamically update running stream thread depending on what changed
    if camera_in.rtsp_url and camera_in.rtsp_url != old_url:
        stream_processor_manager.start_camera_stream(
            camera_id=str(updated_camera.id),
            rtsp_url=updated_camera.rtsp_url,
            name=updated_camera.name
        )
    elif camera_in.rois is not None:
        stream_processor_manager.update_camera_rois(
            camera_id=str(updated_camera.id),
            rois=updated_camera.rois
        )

    return updated_camera

@router.delete("/{id}")
async def delete_camera(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = CameraRepository(db)
    
    # Dynamic thread cleanup first
    stream_processor_manager.stop_camera_stream(str(id))
    
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found.")
    
    await db.commit()
    return {"message": "Camera deleted successfully"}

@router.get("/status/live", response_model=List[CameraStatusResponse])
async def get_cameras_live_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Returns the live in-memory stats (FPS, status) for all cameras."""
    repo = CameraRepository(db)
    cameras = await repo.list()
    
    results = []
    import datetime
    for c in cameras:
        live = camera_manager.get_live_status(str(c.id))
        results.append({
            "id": c.id,
            "name": c.name,
            "status": live["status"],
            "fps": live["fps"],
            "last_seen": datetime.datetime.fromtimestamp(live["last_seen"], tz=datetime.timezone.utc)
        })
    return results

import cv2
import asyncio
import numpy as np
from fastapi.responses import StreamingResponse
from app.services.video_manager import video_manager

@router.get("/{id}/stream")
async def stream_camera(id: UUID) -> Any:
    """Streams the live processed camera feed as MJPEG."""
    camera_str_id = str(id)
    
    async def frame_generator():
        # Prepare a simple black frame if camera is offline
        offline_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(offline_frame, "Camera Stream Offline", (160, 180), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        _, offline_jpeg = cv2.imencode('.jpg', offline_frame)
        offline_bytes = offline_jpeg.tobytes()
        
        while True:
            # Check if there is an active buffer for this camera and it contains frames
            if camera_str_id in video_manager.buffers and len(video_manager.buffers[camera_str_id]) > 0:
                try:
                    # Get the latest frame in the deque (the newest frame)
                    timestamp, jpeg_bytes = video_manager.buffers[camera_str_id][-1]
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                except Exception:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + offline_bytes + b'\r\n')
            else:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + offline_bytes + b'\r\n')
            
            # Rate limit to ~15 FPS to prevent resource hogs
            await asyncio.sleep(0.066)
            
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
