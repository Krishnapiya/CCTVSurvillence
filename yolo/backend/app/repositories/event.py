from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.event import Event, VideoClip, Snapshot
from app.models.verification import EventVerification
from app.repositories.base import BaseRepository

class EventRepository(BaseRepository[Event]):
    def __init__(self, db: AsyncSession):
        super().__init__(Event, db)

    async def get_with_relations(self, id: UUID) -> Optional[Event]:
        stmt = (
            select(Event)
            .filter(Event.id == id)
            .options(
                selectinload(Event.alert),
                selectinload(Event.verifications),
                selectinload(Event.video_clip_rel),
                selectinload(Event.snapshot_rel),
                selectinload(Event.camera)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_events_filtered(
        self,
        camera_id: Optional[UUID] = None,
        event_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        filters = []
        if camera_id:
            filters.append(Event.camera_id == camera_id)
        if event_type:
            filters.append(Event.type == event_type)
        if min_confidence is not None:
            filters.append(Event.confidence >= min_confidence)
        if start_time:
            filters.append(Event.timestamp >= start_time)
        if end_time:
            filters.append(Event.timestamp <= end_time)

        stmt = (
            select(Event)
            .filter(and_(*filters))
            .options(
                selectinload(Event.alert),
                selectinload(Event.verifications),
                selectinload(Event.video_clip_rel),
                selectinload(Event.snapshot_rel)
            )
            .order_by(Event.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class VideoClipRepository(BaseRepository[VideoClip]):
    def __init__(self, db: AsyncSession):
        super().__init__(VideoClip, db)

class SnapshotRepository(BaseRepository[Snapshot]):
    def __init__(self, db: AsyncSession):
        super().__init__(Snapshot, db)

class EventVerificationRepository(BaseRepository[EventVerification]):
    def __init__(self, db: AsyncSession):
        super().__init__(EventVerification, db)

    async def get_by_event(self, event_id: UUID) -> List[EventVerification]:
        stmt = select(EventVerification).filter(EventVerification.event_id == event_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
