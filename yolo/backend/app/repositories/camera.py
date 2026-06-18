from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.camera import Camera, CameraGroup
from app.repositories.base import BaseRepository

class CameraGroupRepository(BaseRepository[CameraGroup]):
    def __init__(self, db: AsyncSession):
        super().__init__(CameraGroup, db)

    async def get_by_name(self, name: str) -> Optional[CameraGroup]:
        result = await self.db.execute(select(CameraGroup).filter(CameraGroup.name == name))
        return result.scalars().first()

class CameraRepository(BaseRepository[Camera]):
    def __init__(self, db: AsyncSession):
        super().__init__(Camera, db)

    async def get_by_name(self, name: str) -> Optional[Camera]:
        result = await self.db.execute(select(Camera).filter(Camera.name == name))
        return result.scalars().first()

    async def get_cameras_by_group(self, group_id: UUID) -> List[Camera]:
        result = await self.db.execute(select(Camera).filter(Camera.camera_group_id == group_id))
        return list(result.scalars().all())
