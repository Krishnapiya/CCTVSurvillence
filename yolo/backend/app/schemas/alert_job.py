from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

class AlertJobBase(BaseModel):
    name: str
    event_type: str
    start_time: str
    end_time: str
    days: List[str]
    camera_ids: List[str]
    is_active: Optional[bool] = True

class AlertJobCreate(AlertJobBase):
    pass

class AlertJobUpdate(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    days: Optional[List[str]] = None
    camera_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AlertJobResponse(AlertJobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
