import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class CameraGroup(Base):
    __tablename__ = "camera_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    cameras = relationship("Camera", back_populates="group", cascade="all, delete-orphan")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)
    rtsp_url = Column(String, nullable=False)
    status = Column(String, default="offline", nullable=False)  # online, offline, error
    ip_address = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    rois = Column(JSON, default=list, nullable=False)
    camera_group_id = Column(UUID(as_uuid=True), ForeignKey("camera_groups.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    group = relationship("CameraGroup", back_populates="cameras")
    events = relationship("Event", back_populates="camera", cascade="all, delete-orphan")
