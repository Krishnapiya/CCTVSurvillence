import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class EventVerification(Base):
    __tablename__ = "event_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String, nullable=False)  # Qwen2.5-VL, CLIP, MoViNet, MoveNet
    result = Column(String, nullable=False)  # VERIFIED, REFUTED, UNCERTAIN
    confidence = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)  # Detailed logs, response text, etc.
    verified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="verifications")
