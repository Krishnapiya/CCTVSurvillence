"""
Build CCTV Master sync payloads from local surveillance records.

Used by the sync agent (next step) to push events and camera logs to HQ.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import settings
from app.models.camera import Camera
from app.models.event import Event
from app.services.event_type_mapping import map_to_master_event_code


def station_context() -> dict[str, str]:
    return {
        "installation_id": settings.INSTALLATION_ID,
        "office_code": settings.OFFICE_CODE,
        "office_name": settings.OFFICE_NAME,
        "master_api_url": settings.MASTER_API_URL,
        "sync_enabled": settings.SYNC_ENABLED,
    }


def master_event_id(surveillance_event_id) -> str:
    """Stable event_id for master — prefix avoids collisions across stations."""
    return f"EVT-{surveillance_event_id}"


def camera_code_for_sync(camera: Camera) -> str:
    """Master uses camera_code string; surveillance uses UUID — use short stable id."""
    return str(camera.id)


def build_master_event_payload(event: Event, camera: Camera) -> dict[str, Any] | None:
    """
    Convert a surveillance Event + Camera into CCTV Master EventBase shape.
    Returns None if event type cannot be mapped to a master event_code.
    """
    event_code = map_to_master_event_code(event.type)
    if not event_code:
        return None

    return {
        "event_id": master_event_id(event.id),
        "event_code": event_code,
        "time_of_occurrence": event.timestamp.isoformat(),
        "video_clip": None,  # set after POST /api/sync/clips/{event_id}
        "installation_id": settings.INSTALLATION_ID,
        "camera_code": camera_code_for_sync(camera),
        "camera_name": camera.name,
        "camera_location": camera.location,
        "office_name": settings.OFFICE_NAME,
        "roi_name": event.roi_name,
        "confidence": f"{event.confidence:.4f}",
    }


def build_master_camera_log_payload(camera: Camera, last_seen: datetime | None = None) -> dict[str, Any]:
    """Convert surveillance camera status into CCTV Master CameraLogBase shape."""
    status = camera.status if camera.status in ("online", "offline") else "offline"
    return {
        "installation_id": settings.INSTALLATION_ID,
        "camera_code": camera_code_for_sync(camera),
        "camera_name": camera.name,
        "status": status,
        "last_received_time": (last_seen or camera.updated_at).isoformat()
        if (last_seen or camera.updated_at)
        else None,
    }
