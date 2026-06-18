from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.repositories.alert import AlertRepository
from app.repositories.camera import CameraRepository
from app.repositories.event import EventRepository
from app.schemas.report import ReportsSummaryResponse
from app.api import deps
from app.models.user import User
from app.models.event import Event
from app.models.camera import Camera

router = APIRouter()

@router.get("/summary", response_model=ReportsSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    alert_repo = AlertRepository(db)
    camera_repo = CameraRepository(db)

    # 1. Alert counts by status and severity
    alert_stats = await alert_repo.get_alert_statistics()

    # 2. Event counts by type
    event_stmt = select(Event.type, func.count(Event.id)).group_by(Event.type)
    event_res = await db.execute(event_stmt)
    event_type_counts = {ev_type: count for ev_type, count in event_res.all()}

    # 3. Camera statuses count
    camera_stmt = select(Camera.status, func.count(Camera.id)).group_by(Camera.status)
    camera_res = await db.execute(camera_stmt)
    camera_status_counts = {status: count for status, count in camera_res.all()}

    # Guarantee essential fields exist in response dicts
    by_status = {"CREATED": 0, "ACKNOWLEDGED": 0, "RESOLVED": 0}
    by_status.update(alert_stats["by_status"])

    by_severity = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    by_severity.update(alert_stats["by_severity"])

    return {
        "total_alerts": alert_stats["total_alerts"],
        "by_status": by_status,
        "by_severity": by_severity,
        "by_event_type": event_type_counts,
        "camera_status_counts": camera_status_counts
    }
