import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def list_views():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(
            "SELECT viewname FROM pg_catalog.pg_views WHERE schemaname='public';"
        ))
        views = [row[0] for row in result.fetchall()]
        print("=" * 60)
        print("DATABASE VIEWS:")
        print("=" * 60)
        for v in views:
            print(f"- {v}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(list_views())
