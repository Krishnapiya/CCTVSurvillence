import asyncio
import asyncpg

async def main():
    db_url = "postgresql://postgres:password@localhost:5432/surveillance_system"
    print(f"Connecting to database: {db_url}")
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected successfully. Adding 'roi_name' column to 'events' table...")
        
        # Add columns if not exists
        await conn.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS roi_name VARCHAR;")
        await conn.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS master_synced_at TIMESTAMP WITH TIME ZONE;")
        await conn.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS master_clip_synced_at TIMESTAMP WITH TIME ZONE;")
        print("Columns added successfully.")
        
        # Verify the columns in the events table
        rows = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'events';
        """)
        print("\nCurrent columns in 'events' table:")
        for r in rows:
            print(f"- {r['column_name']}: {r['data_type']}")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
