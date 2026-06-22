import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # fire, smoke, mobile_usage, intrusion, uniform_violation, smoking, fight, fainting, suicide_risk, projectile
    confidence = Column(Float, nullable=False)
    roi_name = Column(String, nullable=True)
    snapshot_path = Column(String, nullable=True)
    video_clip_path = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    camera = relationship("Camera", back_populates="events")
    alert = relationship("Alert", back_populates="event", uselist=False, cascade="all, delete-orphan")
    verifications = relationship("EventVerification", back_populates="event", cascade="all, delete-orphan")
    video_clip_rel = relationship("VideoClip", back_populates="event", uselist=False, cascade="all, delete-orphan")
    snapshot_rel = relationship("Snapshot", back_populates="event", uselist=False, cascade="all, delete-orphan")

class VideoClip(Base):
    __tablename__ = "video_clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    duration_seconds = Column(Float, default=10.0)
    start_timestamp = Column(DateTime(timezone=True), nullable=False)
    end_timestamp = Column(DateTime(timezone=True), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="video_clip_rel")

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    resolution = Column(String, nullable=True)  # e.g., "1920x1080"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="snapshot_rel")
