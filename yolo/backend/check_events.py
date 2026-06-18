import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.event import EventRepository

async def check_events():
    async with AsyncSessionLocal() as session:
        repo = EventRepository(session)
        events = await repo.list(limit=100)
        print("=" * 60)
        print(f"EVENTS IN DATABASE ({len(events)} total)")
        print("=" * 60)
        for idx, e in enumerate(events):
            print(f"{idx+1}. Camera: {e.camera_id}")
            print(f"   ID: {e.id}")
            print(f"   Type: {e.type}")
            print(f"   Confidence: {e.confidence}")
            print(f"   Timestamp: {e.timestamp}")
            print("-" * 40)
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_events())
