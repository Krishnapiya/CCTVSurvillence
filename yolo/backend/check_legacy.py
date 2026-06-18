import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_legacy():
    async with AsyncSessionLocal() as session:
        for table in ["event_logs", "camera_profiles", "rois", "roi_events"]:
            try:
                res = await session.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = res.scalar()
                print(f"Table '{table}': {count} rows")
            except Exception as e:
                print(f"Failed to check '{table}': {e}")

if __name__ == "__main__":
    asyncio.run(check_legacy())
