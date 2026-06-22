from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.camera import Camera, CameraGroup
from app.repositories.base import BaseRepository
from app.utils.camera_code import format_camera_code, normalize_camera_code

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

    async def get_by_camera_code(self, camera_code: str) -> Optional[Camera]:
        code = normalize_camera_code(camera_code)
        result = await self.db.execute(select(Camera).filter(Camera.camera_code == code))
        return result.scalars().first()

    async def allocate_next_camera_code(self) -> str:
        result = await self.db.execute(select(Camera.camera_code))
        max_sequence = 0
        for code in result.scalars().all():
            if not code or not code.startswith("CAM-"):
                continue
            suffix = code[4:]
            if suffix.isdigit():
                max_sequence = max(max_sequence, int(suffix))
        return format_camera_code(max_sequence + 1)

    async def get_cameras_by_group(self, group_id: UUID) -> List[Camera]:
        result = await self.db.execute(select(Camera).filter(Camera.camera_group_id == group_id))
        return list(result.scalars().all())
