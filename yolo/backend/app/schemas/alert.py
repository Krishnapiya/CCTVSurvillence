from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from app.schemas.event import EventResponse

class AlertResponse(BaseModel):
    id: UUID
    event_id: UUID
    status: str
    severity: str
    assigned_to: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    event: Optional[EventResponse] = None

    class Config:
        from_attributes = True

class AlertUpdate(BaseModel):
    status: Optional[str] = None  # CREATED, ACKNOWLEDGED, RESOLVED
    severity: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL
