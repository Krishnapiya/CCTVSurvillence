import os
import shutil
import asyncio
import asyncpg
from uuid import UUID
from app.workers.tasks import process_event_clip_and_verify

async def get_latest_event():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    row = await conn.fetchrow("SELECT id, camera_id, type, snapshot_path FROM events ORDER BY created_at DESC LIMIT 1")
    await conn.close()
    return row

async def check_database_verification(event_id):
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/surveillance_system")
    row = await conn.fetchrow("SELECT video_clip_path FROM events WHERE id = $1", UUID(event_id))
    await conn.close()
    return row

def main():
    # 1. Fetch latest event
    row = asyncio.run(get_latest_event())
    if not row:
        print("No events found in database to test with.")
        return
        
    event_id = str(row['id'])
    camera_id = str(row['camera_id'])
    event_type = row['type']
    snapshot_path = row['snapshot_path']
    
    print(f"Testing with Event: {event_id}, Camera: {camera_id}, Type: {event_type}, Snapshot: {snapshot_path}")
    
    # 2. Create mock frames directory
    temp_dir = f"./media/temp_test_{event_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Copy snapshot as dummy frames
    if os.path.exists(snapshot_path):
        for i in range(30): # 2 seconds of video at 15fps
            shutil.copy(snapshot_path, os.path.join(temp_dir, f"frame_{i:03d}.jpg"))
    else:
        print(f"Warning: snapshot file {snapshot_path} not found. Generating mock frames.")
        import cv2
        import numpy as np
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "TEST FRAME", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        for i in range(30):
            cv2.imwrite(os.path.join(temp_dir, f"frame_{i:03d}.jpg"), img)
            
    # Write sentinel complete.txt
    with open(os.path.join(temp_dir, "complete.txt"), "w") as f:
        f.write("done")
        
    print(f"Mock frames created in {temp_dir}. Invoking process_event_clip_and_verify...")
    
    # 3. Invoke task
    process_event_clip_and_verify(
        event_id=event_id,
        camera_id=camera_id,
        temp_frames_dir=temp_dir,
        event_type=event_type,
        snapshot_path=snapshot_path
    )
    
    # 4. Verify in DB
    updated_row = asyncio.run(check_database_verification(event_id))
    print(f"\nVerification Results:")
    print(f"- Video Clip Path in DB: {updated_row['video_clip_path']}")
    
    # Verify clip file
    if updated_row['video_clip_path'] and os.path.exists(updated_row['video_clip_path']):
        size = os.path.getsize(updated_row['video_clip_path'])
        print(f"- Video Clip File exists! Size: {size} bytes")
    else:
        print(f"- Video Clip File NOT found at {updated_row['video_clip_path']}")

if __name__ == "__main__":
    main()
