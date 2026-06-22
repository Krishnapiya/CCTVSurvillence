"""
Push surveillance station data to the CCTV Master dashboard at HQ.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.camera import CameraRepository
from app.repositories.event import EventRepository
from app.services.event_type_mapping import is_syncable_event_type
from app.services.master_sync_payload import (
    build_master_camera_log_payload,
    build_master_event_payload,
    master_event_id,
)
from app.services.video_transcode import ensure_web_playable_clip, normalize_media_path

logger = logging.getLogger("master_sync")


def _sync_headers() -> dict[str, str]:
    return {"X-API-Key": settings.SYNC_API_KEY}


def _events_url() -> str:
    return f"{settings.MASTER_API_URL.rstrip('/')}/events"


def _logs_url() -> str:
    return f"{settings.MASTER_API_URL.rstrip('/')}/logs"


def _clips_url(event_id: str) -> str:
    return f"{settings.MASTER_API_URL.rstrip('/')}/clips/{event_id}"


def _resolve_clip_path(video_clip_path: str | None) -> str | None:
    if not video_clip_path:
        return None
    path = normalize_media_path(video_clip_path, settings.MEDIA_STORAGE_DIR)
    if not path or not os.path.exists(path):
        return None
    playable = ensure_web_playable_clip(path)
    return playable if playable and os.path.exists(playable) else None


async def push_camera_logs(client: httpx.AsyncClient, db: AsyncSession) -> dict[str, int]:
    camera_repo = CameraRepository(db)
    cameras = await camera_repo.list(limit=500)
    if not cameras:
        return {"pushed": 0}

    logs = [build_master_camera_log_payload(camera) for camera in cameras]
    response = await client.post(_logs_url(), json={"logs": logs})
    response.raise_for_status()
    data = response.json()
    logger.info("Master sync: camera logs pushed (%s)", data)
    return {"pushed": len(logs)}


async def push_pending_events(client: httpx.AsyncClient, db: AsyncSession) -> dict[str, int]:
    event_repo = EventRepository(db)
    pending = await event_repo.list_pending_master_sync(limit=50)

    synced = 0
    skipped = 0
    failed = 0
    now = datetime.now(timezone.utc)
    dirty = False

    for event in pending:
        if not is_syncable_event_type(event.type):
            skipped += 1
            continue

        camera = event.camera
        if not camera:
            logger.warning("Master sync: event %s has no camera, skipping", event.id)
            failed += 1
            continue

        payload = build_master_event_payload(event, camera)
        if not payload:
            skipped += 1
            continue

        try:
            response = await client.post(_events_url(), json={"events": [payload]})
            response.raise_for_status()
            event.master_synced_at = now
            synced += 1
            dirty = True
            logger.info(
                "Master sync: event %s -> %s",
                event.id,
                master_event_id(event.id),
            )
        except httpx.HTTPError as exc:
            failed += 1
            logger.error("Master sync: failed event %s: %s", event.id, exc)

    if dirty:
        await db.commit()

    return {"synced": synced, "skipped": skipped, "failed": failed}


async def push_pending_clips(client: httpx.AsyncClient, db: AsyncSession) -> dict[str, int]:
    event_repo = EventRepository(db)
    pending = await event_repo.list_pending_clip_sync(limit=20)

    uploaded = 0
    skipped = 0
    failed = 0
    now = datetime.now(timezone.utc)
    dirty = False

    for event in pending:
        clip_path = _resolve_clip_path(event.video_clip_path)
        if not clip_path:
            skipped += 1
            continue

        mid = master_event_id(event.id)
        try:
            with open(clip_path, "rb") as clip_file:
                response = await client.post(
                    _clips_url(mid),
                    data={"installation_id": settings.INSTALLATION_ID},
                    files={"file": (os.path.basename(clip_path), clip_file, "video/mp4")},
                )
            response.raise_for_status()
            event.master_clip_synced_at = now
            uploaded += 1
            dirty = True
            logger.info("Master sync: clip uploaded for %s", mid)
        except httpx.HTTPError as exc:
            failed += 1
            logger.error("Master sync: clip upload failed for %s: %s", mid, exc)
        except OSError as exc:
            failed += 1
            logger.error("Master sync: clip read failed for %s: %s", mid, exc)

    if dirty:
        await db.commit()

    return {"uploaded": uploaded, "skipped": skipped, "failed": failed}


async def run_master_sync_cycle() -> dict[str, Any]:
    """Run one full sync cycle: logs -> events -> clips."""
    if not settings.SYNC_ENABLED:
        return {"enabled": False, "message": "Master sync is disabled (SYNC_ENABLED=false)"}

    if not settings.MASTER_API_URL or not settings.SYNC_API_KEY:
        return {"enabled": True, "error": "MASTER_API_URL or SYNC_API_KEY not configured"}

    summary: dict[str, Any] = {
        "enabled": True,
        "installation_id": settings.INSTALLATION_ID,
        "office_code": settings.OFFICE_CODE,
        "master_api_url": settings.MASTER_API_URL,
    }

    timeout = httpx.Timeout(120.0, connect=15.0)
    async with httpx.AsyncClient(headers=_sync_headers(), timeout=timeout) as client:
        async with AsyncSessionLocal() as db:
            try:
                summary["camera_logs"] = await push_camera_logs(client, db)
            except httpx.HTTPError as exc:
                summary["camera_logs"] = {"error": str(exc)}
                logger.error("Master sync: camera logs failed: %s", exc)

        async with AsyncSessionLocal() as db:
            try:
                summary["events"] = await push_pending_events(client, db)
            except httpx.HTTPError as exc:
                summary["events"] = {"error": str(exc)}
                logger.error("Master sync: events failed: %s", exc)

        async with AsyncSessionLocal() as db:
            try:
                summary["clips"] = await push_pending_clips(client, db)
            except httpx.HTTPError as exc:
                summary["clips"] = {"error": str(exc)}
                logger.error("Master sync: clips failed: %s", exc)

    return summary
