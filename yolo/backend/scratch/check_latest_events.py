import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    rows = await conn.fetch("SELECT id, type, video_clip_path, snapshot_path, created_at FROM events ORDER BY created_at DESC LIMIT 5")
    print("LATEST EVENTS:")
    for row in rows:
        print(f"- ID: {row['id']}, Type: {row['type']}, VideoPath: {row['video_clip_path']}, SnapshotPath: {row['snapshot_path']}, CreatedAt: {row['created_at']}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
