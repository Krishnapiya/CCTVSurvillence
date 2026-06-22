from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

class CameraGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class CameraGroupCreate(CameraGroupBase):
    pass

class CameraGroupResponse(CameraGroupBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CameraBase(BaseModel):
    name: str
    rtsp_url: str
    camera_group_id: Optional[UUID] = None
    location: Optional[str] = None
    rois: Optional[List[dict]] = []

class CameraCreate(CameraBase):
    camera_code: Optional[str] = None

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    camera_code: Optional[str] = None
    rtsp_url: Optional[str] = None
    camera_group_id: Optional[UUID] = None
    location: Optional[str] = None
    status: Optional[str] = None
    rois: Optional[List[dict]] = None

class CameraResponse(CameraBase):
    id: UUID
    camera_code: str
    status: str
    created_at: datetime
    updated_at: datetime
    rois: List[dict] = []

    class Config:
        from_attributes = True

class CameraStatusResponse(BaseModel):
    id: UUID
    name: str
    status: str
    fps: float
    last_seen: datetime
