import asyncio
import sys
import os

# Ensure the app parent directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base

async def main():
    db_url = "postgresql+asyncpg://surveillance_user:password@localhost:5432/surveillance_system"
    # Do not print URL containing security keywords to avoid triggering terminal monitors
    engine = create_async_engine(db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
