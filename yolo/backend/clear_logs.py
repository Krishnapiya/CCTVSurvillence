import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def clear_database_logs():
    async with AsyncSessionLocal() as db:
        print("Clearing events, alerts, snapshots, video_clips, and event_verifications tables using DELETE...")
        await db.execute(text("DELETE FROM alerts;"))
        await db.execute(text("DELETE FROM snapshots;"))
        await db.execute(text("DELETE FROM video_clips;"))
        await db.execute(text("DELETE FROM event_verifications;"))
        await db.execute(text("DELETE FROM events;"))
        await db.commit()
        print("Database logs cleared successfully.")

if __name__ == "__main__":
    asyncio.run(clear_database_logs())
