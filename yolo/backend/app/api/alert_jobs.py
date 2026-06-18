from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.alert_job import AlertJobRepository
from app.schemas.alert_job import AlertJobResponse, AlertJobCreate, AlertJobUpdate
from app.api import deps
from app.models.user import User

router = APIRouter()

@router.get("", response_model=List[AlertJobResponse])
async def list_alert_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = AlertJobRepository(db)
    return await repo.list(limit=1000)

@router.post("", response_model=AlertJobResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_job(
    *,
    db: AsyncSession = Depends(get_db),
    job_in: AlertJobCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = AlertJobRepository(db)
    job = await repo.create(job_in.dict())
    await db.commit()
    return job

@router.put("/{id}", response_model=AlertJobResponse)
async def update_alert_job(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    job_in: AlertJobUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = AlertJobRepository(db)
    job = await repo.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="Alert Job not found.")
    updated_job = await repo.update(job, job_in.dict(exclude_unset=True))
    await db.commit()
    return updated_job

@router.delete("/{id}", response_model=bool)
async def delete_alert_job(
    *,
    db: AsyncSession = Depends(get_db),
    id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    repo = AlertJobRepository(db)
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert Job not found.")
    await db.commit()
    return True
