# SentryPose AI - CCTV Fall and Fainting Detection System

SentryPose AI is a complete, production-grade CCTV-based Fall and Fainting Detection System. It utilizes **YOLOv11 Pose Estimation** for keypoint extraction, **ByteTrack** for tracking unique person IDs, a **posture analysis state machine** for orientation analysis, **motionless verification** for fainting confidence, **FastAPI** for backend REST endpoints/streaming, **PostgreSQL** for database logging, and a **React dashboard** for live viewing and alert management.

---

## Features

1. **YOLOv11 Pose Tracking**: Auto-detects all persons and tracks them frame-by-frame with unique IDs using ByteTrack.
2. **Angle & Aspect-Ratio Posture Engine**: Classifies posture dynamically into `VERTICAL`, `FALLING`, and `HORIZONTAL` using torso vectors and bounding-box ratios.
3. **Transition State Machine**: Validates transitions (`VERTICAL` $\rightarrow$ `FALLING` $\rightarrow$ `HORIZONTAL`) within a 3.0s window to isolate sudden falls.
4. **Motionless Verification**: Analyzes standard deviation of coordinates for 5 seconds after a fall to verify still/unconscious states (ignoring temporary lying positions).
5. **Velocity Analysis**: Computes vertical downward speed ($V_y$) to increase incident confidence on rapid collapses.
6. **Media Recording**: Saves annotated screenshots and extracts 15-second event video clips (10s pre-event buffer + 5s post-event) dynamically when alerts trigger.
7. **Robust PostgreSQL Integration**: Logs incident timestamps, coordinates, confidence levels, and paths with a built-in in-memory fallback for local testing without running database servers.
8. **Dual React Dashboard**: Provides a gorgeous dark-themed dashboard. Runs as a standalone React app or is served directly from the FastAPI root URL `/` (requires no node installation!).

---

## Installation & Setup

### 1. Prerequisites
- **Python**: Version 3.11 or higher
- **Node.js & npm**: (Optional, only needed to run Vite standalone frontend)
- **PostgreSQL**: (Optional, system falls back to in-memory testing if database connection is absent)

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```
*(This installs FastAPI, Uvicorn, OpenCV, Ultralytics YOLO, PostgreSQL adapter, Pydantic settings, etc.)*

### 3. PostgreSQL Database Setup (Optional)
If using a local PostgreSQL database:
1. Create a database named `fall_detection`.
2. Execute the table schema:
   ```bash
   psql -U postgres -d fall_detection -f schema.sql
   ```
3. Set your credentials in environment variables or configure them in `.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=fall_detection
   DB_USER=postgres
   DB_PASSWORD=postgres
   ```

---

## How to Run

### 1. Run Automated Test Suite
Verify the entire system logic (database fallback, posture analyzer, transition state machine, motionless timer, and video writer) with simulated keypoint and coordinates data:
```bash
python test_workflow.py
```
This runs a simulated fall sequence and outputs logs proving transition tracking and event confirmation.

### 2. Start the Backend API & Processing Server
Start the backend orchestrator. By default, it uses the local webcam (ID `0`).
```bash
python main.py
```
*To use a custom video file or RTSP stream, edit `config.py` or set the environment variable:*
```bash
export VIDEO_SOURCE="/path/to/cctv_recording.mp4"
python main.py
```
Or for RTSP:
```bash
export VIDEO_SOURCE="rtsp://admin:pass@192.168.1.100:554/stream1"
python main.py
```

### 3. Open the Dashboard
- **FastAPI Direct Route**: Open your browser and navigate to:
  `http://localhost:8000/`
  *(This displays the full React-based SentryPose Dashboard rendered directly from the server!)*
- **Standalone React App (Vite)**:
  If you want to run the dev server separately:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Then navigate to `http://localhost:3000/`.

---

## Project Architecture & Modular Components

- **`config.py`**: Configures YOLO confidence thresholds, fall angle, motionless timer, alert cooldown, and Postgres connections.
- **`database.py`**: Interacts with PostgreSQL. Implements automatic in-memory mock fallback to support database-free local execution.
- **`detector.py`**: Loads and coordinates YOLOv11 Pose model. Automatically fetches the official `yolo11n-pose.pt` weights.
- **`tracker.py`**: Integrates ByteTrack tracking wrapper to sustain unique IDs.
- **`posture.py`**: Calculates torso incline angles (using shoulder and hip midpoints) and aspect ratios.
- **`state_machine.py`**: Tracks state histories per person and computes fall transition triggers.
- **`motion.py`**: Measures coordinate standard deviations (stillness) and vertical velocities.
- **`alert.py`**: Coordinates background video writing threads, saves images/JSON logs, and handles Linux sound alerts.
- **`api.py`**: FastAPI routes serving video streams, lists, and static assets.
- **`main.py`**: Video capturing loop, drawing of HUD overlays, and server startup.
