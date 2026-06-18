from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert_job import AlertJob
from app.repositories.base import BaseRepository

class AlertJobRepository(BaseRepository[AlertJob]):
    def __init__(self, db: AsyncSession):
        super().__init__(AlertJob, db)
