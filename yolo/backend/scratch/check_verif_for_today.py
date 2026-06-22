import asyncio
import asyncpg
from datetime import datetime, timezone, timedelta

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    
    # Query verifications for today (June 22, 2026 UTC)
    today = datetime(2026, 6, 22, tzinfo=timezone.utc).date()
    rows = await conn.fetch("SELECT * FROM event_verifications WHERE verified_at::date = $1", today)
    print(f"VERIFICATIONS FOR TODAY ({today}):")
    for r in rows:
        print(dict(r))
        
    # Also show recent events from today
    events = await conn.fetch("SELECT id, type, created_at FROM events WHERE created_at::date = $1 ORDER BY created_at DESC", today)
    print(f"\nEVENTS CREATED TODAY ({today}):")
    for e in events:
        print(dict(e))
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
