import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.alert_job import AlertJobRepository

async def show_alert_jobs():
    async with AsyncSessionLocal() as session:
        repo = AlertJobRepository(session)
        jobs = await repo.list(limit=100)
        print("=" * 60)
        print(f"ALERT JOBS IN DATABASE")
        print("=" * 60)
        for idx, j in enumerate(jobs):
            print(f"{idx+1}. Name: {j.name}")
            print(f"   ID: {j.id}")
            print(f"   Camera IDs: {j.camera_ids}")
            print(f"   Event Type: {j.event_type}")
            print("-" * 40)
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(show_alert_jobs())
