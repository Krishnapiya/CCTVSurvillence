from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.camera import CameraRepository
from app.models.camera import Camera

class CameraManager:
    def __init__(self):
        # In-memory status tracking
        # Maps camera_id -> {"status": "online"|"offline", "fps": float, "last_seen": float}
        self.camera_statuses: Dict[str, Dict[str, Any]] = {}

    def update_status(self, camera_id: str, status: str, fps: float = 0.0):
        import time
        self.camera_statuses[camera_id] = {
            "status": status,
            "fps": fps,
            "last_seen": time.time()
        }

    async def persist_status(self, camera_id: str, status: str, db: AsyncSession):
        """Syncs the in-memory camera status to the PostgreSQL database."""
        repo = CameraRepository(db)
        try:
            camera_uuid = UUID(camera_id)
            camera = await repo.get(camera_uuid)
            if camera:
                await repo.update(camera, {"status": status})
                self.update_status(camera_id, status)
        except Exception as e:
            print(f"Error persisting camera status: {e}")

    def get_live_status(self, camera_id: str) -> Dict[str, Any]:
        return self.camera_statuses.get(camera_id, {
            "status": "offline",
            "fps": 0.0,
            "last_seen": 0.0
        })

    def get_all_live_statuses(self) -> Dict[str, Dict[str, Any]]:
        return self.camera_statuses

camera_manager = CameraManager()
