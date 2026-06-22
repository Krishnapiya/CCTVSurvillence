import asyncio
import asyncpg

async def main():
    db_url = "postgresql://postgres:password@localhost:5432/surveillance_system"
    print(f"Connecting to database: {db_url}")
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected successfully.")
        
        # 1. Add camera_code column as nullable first
        await conn.execute("ALTER TABLE cameras ADD COLUMN IF NOT EXISTS camera_code VARCHAR(50);")
        print("Column 'camera_code' added as nullable.")
        
        # 2. Fetch all cameras that have NULL camera_code
        rows = await conn.fetch("SELECT id, name FROM cameras WHERE camera_code IS NULL;")
        print(f"Found {len(rows)} cameras needing code allocation.")
        
        for idx, row in enumerate(rows):
            cam_id = row['id']
            code = f"CAM-{idx+1:02d}"
            print(f"Allocating code {code} to camera {row['name']} ({cam_id})")
            await conn.execute("UPDATE cameras SET camera_code = $1 WHERE id = $2;", code, cam_id)
            
        # 3. Alter column to be NOT NULL now that it is backfilled
        await conn.execute("ALTER TABLE cameras ALTER COLUMN camera_code SET NOT NULL;")
        print("Altered 'camera_code' to NOT NULL.")
        
        # 4. Create unique index
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_cameras_camera_code ON cameras(camera_code);")
        print("Unique index ix_cameras_camera_code created.")
        
        # Verify the columns in the cameras table
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'cameras';
        """)
        print("\nUpdated columns in 'cameras' table:")
        for col in columns:
            print(f"- {col['column_name']}: {col['data_type']} (Nullable: {col['is_nullable']})")
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
