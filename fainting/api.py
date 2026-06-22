import logging
import time
import shutil
import os
from fastapi import FastAPI, Response, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
from config import settings
import database

logger = logging.getLogger("fall_detection.api")

app = FastAPI(
    title="CCTV Fall and Fainting Detection System API",
    description="Backend API for logging events, retrieving logs, and streaming video feed.",
    version="1.0.0"
)

# Enable CORS for React frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store the latest processed frame
latest_annotated_frame = None

def set_latest_frame(frame):
    """
    Set the latest annotated frame for video streaming.
    """
    global latest_annotated_frame
    latest_annotated_frame = frame

def gen_video_stream():
    """
    Generator function that streams the latest annotated frames.
    """
    global latest_annotated_frame
    while True:
        if latest_annotated_frame is not None:
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', latest_annotated_frame)
            if not ret:
                time.sleep(0.03) # ~30 FPS sleep
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            # Limit the frame rate to ~30 FPS to save bandwidth and CPU
            time.sleep(0.033)
        else:
            # If no frame is ready yet, wait briefly
            time.sleep(0.1)

@app.get("/", response_class=HTMLResponse, summary="Serve system visual dashboard")
def get_dashboard():
    """
    Renders and serves the SentryPose AI React CDN dashboard directly.
    """
    dashboard_path = settings.BASE_DIR / "dashboard.html"
    if dashboard_path.exists():
        with open(dashboard_path, 'r') as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>Dashboard HTML not found.</h1>", status_code=404)

@app.get("/health", summary="Health check endpoint")
def health_check():
    """
    Checks the status of the API and PostgreSQL connection.
    """
    db_connection = database.get_db_connection()
    db_status = "connected" if db_connection else "disconnected"
    if db_connection:
        db_connection.close()
        
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": db_status
    }

@app.get("/events", summary="Get list of all events")
def get_events(limit: int = 50):
    """
    Retrieves stored fall/fainting events from the database (or in-memory fallback).
    """
    events = database.get_events(limit)
    return events

@app.get("/latest-event", summary="Get the most recent event")
def get_latest_event():
    """
    Retrieves the latest fall/fainting event.
    """
    event = database.get_latest_event()
    return event

@app.get("/video_feed", summary="Live camera video stream")
def video_feed():
    """
    Streams the live annotated video feed as an MJPEG multipart response.
    """
    return StreamingResponse(
        gen_video_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# Serve saved screenshots and video clips statically so frontend can access them
try:
    app.mount("/events", StaticFiles(directory=str(settings.EVENTS_DIR)), name="events")
    app.mount("/videos", StaticFiles(directory=str(settings.VIDEOS_DIR)), name="videos")
    logger.info(f"Mounted static file directories: {settings.EVENTS_DIR} and {settings.VIDEOS_DIR}")
except Exception as e:
    logger.error(f"Failed to mount static file directories: {e}")

@app.post("/upload", summary="Upload a video file for fall/fainting detection")
async def upload_video(file: UploadFile = File(...)):
    """
    Uploads a video file and dynamically switches the system's processing source to it.
    """
    logger.info(f"Received video upload request: {file.filename}")
    
    upload_dir = settings.VIDEOS_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"uploaded_video{file_ext}"
    saved_path = upload_dir / saved_filename
    
    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update settings to switch source dynamically
        settings.VIDEO_SOURCE = str(saved_path)
        settings.VIDEO_SOURCE_TIMESTAMP = time.time()
        logger.info(f"Successfully saved uploaded video to {saved_path} and switched VIDEO_SOURCE.")
        
        return {
            "status": "success",
            "message": f"Successfully uploaded and switched to {file.filename}",
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        return {
            "status": "error",
            "message": f"Failed to upload video: {str(e)}"
        }
