import asyncio
import asyncpg
from uuid import UUID

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    
    rows = await conn.fetch("SELECT * FROM event_verifications WHERE event_id = 'fef81105-669f-43c7-b5b7-0be71c32b712'")
    print("VERIFICATIONS FOR fef81105-669f-43c7-b5b7-0be71c32b712:")
    for r in rows:
        print(dict(r))
        
    rows2 = await conn.fetch("SELECT * FROM event_verifications WHERE event_id = '194e9feb-2949-41a9-9b7e-ffe6b066bfce'")
    print("\nVERIFICATIONS FOR 194e9feb-2949-41a9-9b7e-ffe6b066bfce:")
    for r in rows2:
        print(dict(r))
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
