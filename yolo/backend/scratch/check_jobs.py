import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    
    cameras = await conn.fetch("SELECT * FROM cameras LIMIT 5")
    print("CAMERAS:")
    for c in cameras:
        print(dict(c))
        
    jobs = await conn.fetch("SELECT * FROM alert_jobs LIMIT 5")
    print("\nALERT JOBS:")
    for j in jobs:
        print(dict(j))
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
