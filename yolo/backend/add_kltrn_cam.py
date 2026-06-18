import asyncio
from app.core.database import SessionLocal
from app.models.camera import Camera
from app.repositories.camera import CameraRepository

async def main():
    async with SessionLocal() as db:
        repo = CameraRepository(db)
        existing = await repo.get_by_name("kltrn")
        if existing:
            print("Camera 'kltrn' already exists in the database.")
            return
        
        camera_data = {
            "name": "kltrn",
            "rtsp_url": "rtsp://swguser:Swguser789@@192.168.13.131:554/Streaming/Channels/101",
            "rois": []
        }
        
        new_cam = await repo.create(camera_data)
        await db.commit()
        print(f"Successfully created camera 'kltrn' with ID: {new_cam.id}")

if __name__ == "__main__":
    asyncio.run(main())
