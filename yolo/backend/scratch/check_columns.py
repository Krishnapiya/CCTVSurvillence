import asyncio
import asyncpg

async def main():
    db_url = "postgresql://postgres:password@localhost:5432/surveillance_system"
    print(f"Connecting to database: {db_url}")
    try:
        conn = await asyncpg.connect(db_url)
        
        # Verify the columns in the cameras table
        rows = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'cameras';
        """)
        print("\nCurrent columns in 'cameras' table:")
        for r in rows:
            print(f"- {r['column_name']}: {r['data_type']}")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
