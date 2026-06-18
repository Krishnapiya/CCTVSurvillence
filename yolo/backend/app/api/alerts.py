from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.alert import AlertRepository
from app.schemas.alert import AlertResponse, AlertUpdate
from app.api import deps
from app.models.user import User
from app.services.alert_manager import alert_manager

router = APIRouter()

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    camera_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = AlertRepository(db)
    return await repo.list_alerts_filtered(
        status=status,
        severity=severity,
        camera_id=camera_id,
        skip=skip,
        limit=limit
    )

@router.get("/{id}", response_model=AlertResponse)
async def get_alert(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = AlertRepository(db)
    alert = await repo.get_with_relations(id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert

@router.patch("/{id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Acknowledge alert and assign it to the requesting operator."""
    alert = await alert_manager.acknowledge_alert(alert_id=id, user_id=current_user.id, db=db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    await db.commit()
    return alert

@router.patch("/{id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Mark the alert as resolved."""
    alert = await alert_manager.resolve_alert(alert_id=id, user_id=current_user.id, db=db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    await db.commit()
    return alert
