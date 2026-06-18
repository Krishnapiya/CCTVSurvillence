import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def list_tables():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [row[0] for row in result.fetchall()]
        print("=" * 60)
        print("DATABASE TABLES:")
        print("=" * 60)
        for t in tables:
            print(f"- {t}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(list_tables())
