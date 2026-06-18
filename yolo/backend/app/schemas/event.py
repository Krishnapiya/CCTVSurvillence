from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from uuid import UUID

class EventVerificationResponse(BaseModel):
    id: UUID
    service_name: str
    result: str
    confidence: float
    details: Optional[Dict[str, Any]] = None
    verified_at: datetime

    class Config:
        from_attributes = True

class VideoClipResponse(BaseModel):
    id: UUID
    file_path: str
    duration_seconds: float
    start_timestamp: datetime
    end_timestamp: datetime
    file_size_bytes: Optional[int] = None

    class Config:
        from_attributes = True

class SnapshotResponse(BaseModel):
    id: UUID
    file_path: str
    resolution: Optional[str] = None

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: UUID
    camera_id: UUID
    type: str
    confidence: float
    snapshot_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    timestamp: datetime
    created_at: datetime
    verifications: List[EventVerificationResponse] = []
    
    class Config:
        from_attributes = True
