from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.repositories.event import EventRepository
from app.schemas.event import EventResponse
from app.api import deps
from app.models.user import User
from app.services.video_transcode import ensure_web_playable_clip, normalize_media_path

router = APIRouter()

@router.get("", response_model=List[EventResponse])
async def list_events(
    db: AsyncSession = Depends(get_db),
    camera_id: Optional[UUID] = Query(None),
    event_type: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Fetch event history with filters."""
    repo = EventRepository(db)
    events = await repo.list_events_filtered(
        camera_id=camera_id,
        event_type=event_type,
        min_confidence=min_confidence,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    return events

@router.get("/{id}/clip")
async def get_event_clip(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user),
):
    """Stream a browser-compatible MP4 clip for an event."""
    repo = EventRepository(db)
    event = await repo.get(id)
    if not event or not event.video_clip_path:
        raise HTTPException(status_code=404, detail="Video clip not found.")

    source_path = normalize_media_path(event.video_clip_path, settings.MEDIA_STORAGE_DIR)
    if not source_path or not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Video clip file missing on server.")

    playable_path = ensure_web_playable_clip(source_path)
    if not playable_path or not os.path.exists(playable_path):
        raise HTTPException(status_code=404, detail="Unable to prepare video clip for playback.")

    filename = os.path.basename(playable_path)
    return FileResponse(
        playable_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=3600"},
    )

@router.get("/{id}", response_model=EventResponse)
async def get_event(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get detail on a specific event including secondary verification runs."""
    repo = EventRepository(db)
    event = await repo.get_with_relations(id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event
