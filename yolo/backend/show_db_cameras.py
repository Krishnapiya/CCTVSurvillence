import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.camera import CameraRepository

async def show_cameras():
    async with AsyncSessionLocal() as session:
        repo = CameraRepository(session)
        cameras = await repo.list()
        print("=" * 60)
        print(f"DATABASE CAMERA LIST (Total: {len(cameras)})")
        print("=" * 60)
        for idx, c in enumerate(cameras):
            print(f"{idx+1}. Name: {c.name}")
            print(f"   ID: {c.id}")
            print(f"   RTSP URL: {c.rtsp_url}")
            print(f"   Status: {c.status}")
            print("-" * 40)
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(show_cameras())
