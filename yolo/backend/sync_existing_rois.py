import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.camera import CameraRepository
from app.repositories.alert_job import AlertJobRepository
from uuid import UUID

async def sync_existing_rois():
    async with AsyncSessionLocal() as session:
        camera_repo = CameraRepository(session)
        job_repo = AlertJobRepository(session)
        
        cameras = await camera_repo.list()
        jobs = await job_repo.list(limit=100)
        
        if not jobs:
            print("No alert jobs in the database to sync.")
            return
            
        # Let's map jobs by name or grab the first job
        first_job = jobs[0]
        print(f"Mapping all legacy client JOB events to database Job ID: {first_job.id} ({first_job.name})")
        
        updated_any = False
        for cam in cameras:
            rois = cam.rois or []
            modified = False
            new_rois = []
            
            for roi in rois:
                events = roi.get("events", [])
                new_events = []
                for ev in events:
                    ev_id = ev.get("id", "")
                    # If it's a legacy client-side ID
                    if "JOB-" in ev_id and str(first_job.id) not in ev_id:
                        # Extract the client job id suffix or just replace it
                        # ID format: E-JOB_ID-CAMERA_ID
                        new_ev_id = f"E-{first_job.id}-{cam.id}"
                        print(f"Updating legacy event ID in Camera {cam.name}: {ev_id} -> {new_ev_id}")
                        ev["id"] = new_ev_id
                        modified = True
                    new_events.append(ev)
                roi["events"] = new_events
                new_rois.append(roi)
                
            if modified:
                cam.rois = new_rois
                # Mark as modified for SQLAlchemy JSON tracking
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(cam, "rois")
                await session.merge(cam)
                updated_any = True
                
        if updated_any:
            await session.commit()
            print("Successfully synced legacy database records!")
        else:
            print("No legacy records required syncing.")

if __name__ == "__main__":
    asyncio.run(sync_existing_rois())
