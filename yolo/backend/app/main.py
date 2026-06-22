import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import Base, engine, AsyncSessionLocal
from app.core.security import get_password_hash
from app.repositories.user import UserRepository
from app.repositories.camera import CameraRepository
from app.services.websocket_manager import ws_manager
from app.services.stream_processor import stream_processor_manager
from app.services.event_engine import event_engine
from app.services.master_sync_scheduler import start_master_sync_background, stop_master_sync_background

# Import routers
from app.api.auth import router as auth_router
from app.api.cameras import router as cameras_router
from app.api.events import router as events_router
from app.api.alerts import router as alerts_router
from app.api.reports import router as reports_router
from app.api.status import router as status_router
from app.api.test_yolo import router as test_yolo_router
from app.api.alert_jobs import router as alert_jobs_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files to serve snapshots and video clips
app.mount("/media", StaticFiles(directory=settings.MEDIA_STORAGE_DIR), name="media")

# Register standard routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(cameras_router, prefix=f"{settings.API_V1_STR}/cameras", tags=["Cameras"])
app.include_router(events_router, prefix=f"{settings.API_V1_STR}/events", tags=["Events"])
app.include_router(alerts_router, prefix=f"{settings.API_V1_STR}/alerts", tags=["Alerts"])
app.include_router(reports_router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(status_router, prefix=f"{settings.API_V1_STR}/status", tags=["System Status"])
app.include_router(test_yolo_router, prefix=f"{settings.API_V1_STR}/test-yolo", tags=["YOLO Testing"])
app.include_router(alert_jobs_router, prefix=f"{settings.API_V1_STR}/alert-jobs", tags=["Alert Jobs"])

# WebSocket Endpoint for real-time alerting
@app.websocket("/api/v1/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for client-side pings or messages
            data = await websocket.receive_text()
            # Echo or process if necessary
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket)

# Startup Events
@app.on_event("startup")
async def startup_event():
    import asyncio
    stream_processor_manager.loop = asyncio.get_running_loop()

    print("Database tables initializing...")
    async with engine.begin() as conn:
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")

    # Create default admin user if none exists
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        admin = await user_repo.get_by_email("admin@surveillance.com")
        if not admin:
            print("Creating default admin account (admin@surveillance.com / admin123)...")
            await user_repo.create({
                "email": "admin@surveillance.com",
                "hashed_password": get_password_hash("admin123"),
                "role": "admin"
            })
            await session.commit()
            print("Default admin created.")

    # Initialize stream processor callback
    stream_processor_manager.set_callback(event_engine.handle_detection)

    # Automatically start decoding streams for all configured cameras
    async with AsyncSessionLocal() as session:
        camera_repo = CameraRepository(session)
        cameras = await camera_repo.list()
        for c in cameras:
            try:
                stream_processor_manager.start_camera_stream(
                    camera_id=str(c.id),
                    rtsp_url=c.rtsp_url,
                    name=c.name
                )
            except Exception as ex:
                print(f"Could not load camera {c.name} on startup: {ex}")

    start_master_sync_background()

# Shutdown Events
@app.on_event("shutdown")
async def shutdown_event():
    await stop_master_sync_background()
    print("Cleaning up camera streams...")
    stream_processor_manager.stop_all()
    print("Backend application stopped.")
