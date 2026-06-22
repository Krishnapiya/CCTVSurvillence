import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    
    events = await conn.fetch("SELECT id, camera_id, type, video_clip_path, snapshot_path, created_at FROM events ORDER BY created_at DESC LIMIT 10")
    print("LATEST EVENTS:")
    for e in events:
        print(f"ID: {e['id']}, Type: {e['type']}, Video: {e['video_clip_path']}, Snapshot: {e['snapshot_path']}, CreatedAt: {e['created_at']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
