import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.camera import CameraRepository

async def show_camera_rois():
    async with AsyncSessionLocal() as session:
        repo = CameraRepository(session)
        cameras = await repo.list()
        print("=" * 60)
        print(f"CAMERA ROIs IN DATABASE")
        print("=" * 60)
        for idx, c in enumerate(cameras):
            print(f"{idx+1}. Name: {c.name}")
            print(f"   ID: {c.id}")
            print(f"   ROIs: {c.rois}")
            print("-" * 40)
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(show_camera_rois())
