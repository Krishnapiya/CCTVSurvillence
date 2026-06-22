import asyncio
import asyncpg
import json

async def main():
    db_url = "postgresql://postgres:password@localhost:5432/surveillance_system"
    print(f"Connecting to database: {db_url}")
    try:
        conn = await asyncpg.connect(db_url)
        
        print("\n=== CAMERAS ===")
        cameras = await conn.fetch("SELECT id, name, rtsp_url, rois FROM cameras;")
        for cam in cameras:
            print(f"ID: {cam['id']}")
            print(f"Name: {cam['name']}")
            print(f"RTSP: {cam['rtsp_url']}")
            try:
                rois = json.loads(cam['rois']) if isinstance(cam['rois'], str) else cam['rois']
                print(f"ROIs: {json.dumps(rois, indent=2)}")
            except Exception as e:
                print(f"ROIs error: {e}, value: {cam['rois']}")
            print("-" * 50)
            
        print("\n=== ALERT JOBS ===")
        jobs = await conn.fetch("SELECT id, name, event_type, camera_ids FROM alert_jobs;")
        for job in jobs:
            print(f"ID: {job['id']}")
            print(f"Name: {job['name']}")
            print(f"Events: {job['event_type']}")
            print(f"Camera IDs: {job['camera_ids']}")
            print("-" * 50)
            
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
