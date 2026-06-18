from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.alert import Alert
from app.models.event import Event
from app.repositories.base import BaseRepository

class AlertRepository(BaseRepository[Alert]):
    def __init__(self, db: AsyncSession):
        super().__init__(Alert, db)

    async def get_with_relations(self, id: UUID) -> Optional[Alert]:
        stmt = (
            select(Alert)
            .filter(Alert.id == id)
            .options(
                selectinload(Alert.event).selectinload(Event.camera),
                selectinload(Alert.assigned_user)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_alerts_filtered(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        camera_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Alert]:
        filters = []
        if status:
            filters.append(Alert.status == status)
        if severity:
            filters.append(Alert.severity == severity)
        
        if camera_id:
            # We join with Event to filter by camera_id
            stmt = (
                select(Alert)
                .join(Event)
                .filter(and_(Event.camera_id == camera_id, *filters))
                .options(
                    selectinload(Alert.event).selectinload(Event.camera),
                    selectinload(Alert.assigned_user)
                )
                .order_by(Alert.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
        else:
            stmt = (
                select(Alert)
                .filter(and_(*filters))
                .options(
                    selectinload(Alert.event).selectinload(Event.camera),
                    selectinload(Alert.assigned_user)
                )
                .order_by(Alert.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_alert_statistics(self) -> Dict[str, Any]:
        # Count by status
        status_stmt = select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        status_res = await self.db.execute(status_stmt)
        status_counts = {status: count for status, count in status_res.all()}

        # Count by severity
        severity_stmt = select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
        severity_res = await self.db.execute(severity_stmt)
        severity_counts = {severity: count for severity, count in severity_res.all()}

        # Total count
        total_stmt = select(func.count(Alert.id))
        total_res = await self.db.execute(total_stmt)
        total_count = total_res.scalar_one()

        return {
            "total_alerts": total_count,
            "by_status": status_counts,
            "by_severity": severity_counts
        }
