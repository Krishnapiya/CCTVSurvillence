# Surveillance System with ROI-Based Alerts - Software Design Document

## 1. Project Overview

### 1.1 Purpose
Design and implement a comprehensive surveillance system that supports multiple camera profiles with Region of Interest (ROI) based event detection and alerting.

### 1.2 Key Features
- Multiple camera profiles connected to a common DVR
- Manual polygon drawing for ROI definition
- Time-based event scheduling within ROIs
- Multi-ROI support per camera
- Voice alert system for triggered events
- Video clip storage and retrieval
- CRUD operations for profiles, ROIs, and events

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Web/Mobile)  │◄──►│   (API Server)  │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DVR System    │    │   Video Storage │    │   Audio Storage │
│   (RTSP/HTTP)   │    │   (File System) │    │   (File System) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Technology Stack

#### Frontend
- **Framework**: React.js with TypeScript
- **State Management**: Redux Toolkit
- **UI Components**: Material-UI or Ant Design
- **Canvas Drawing**: Fabric.js or Konva.js for polygon drawing
- **Video Streaming**: WebRTC or HLS.js
- **Real-time Communication**: Socket.io-client

#### Backend
- **Framework**: Python with FastAPI
- **Authentication**: JWT tokens with python-jose
- **Real-time**: Socket.io with python-socketio
- **Video Processing**: OpenCV, FFmpeg, and YOLOv5/v11
- **AI/ML**: PyTorch, Ultralytics YOLO, NumPy
- **Scheduling**: Celery with Redis broker
- **API Documentation**: FastAPI auto-generated OpenAPI/Swagger
- **Async Processing**: asyncio and aiofiles

#### Database
- **Primary**: PostgreSQL for relational data
- **Cache**: Redis for session management and real-time data
- **File Storage**: Local filesystem or cloud storage (AWS S3)

## 3. Data Models

### 3.1 Database Schema

#### Camera Profile
```sql
CREATE TABLE camera_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    dvr_connection_string VARCHAR(255) NOT NULL,
    rtsp_url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Region of Interest (ROI)
```sql
CREATE TABLE rois (
    id SERIAL PRIMARY KEY,
    camera_profile_id INTEGER REFERENCES camera_profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    polygon_coordinates JSONB NOT NULL, -- Array of {x, y} points
    color VARCHAR(7) DEFAULT '#FF0000', -- Hex color for visualization
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Event Types
```sql
CREATE TABLE event_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    default_voice_alert_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### ROI Events
```sql
CREATE TABLE roi_events (
    id SERIAL PRIMARY KEY,
    roi_id INTEGER REFERENCES rois(id) ON DELETE CASCADE,
    event_type_id INTEGER REFERENCES event_types(id),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week JSONB NOT NULL, -- [1,2,3,4,5] for Mon-Fri
    is_active BOOLEAN DEFAULT true,
    voice_alert_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Event Logs
```sql
CREATE TABLE event_logs (
    id SERIAL PRIMARY KEY,
    roi_id INTEGER REFERENCES rois(id),
    event_type_id INTEGER REFERENCES event_types(id),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_clip_path VARCHAR(255),
    confidence_score FLOAT,
    thumbnail_path VARCHAR(255),
    is_alert_sent BOOLEAN DEFAULT false
);
```

### 3.2 Data Transfer Objects (DTOs)

#### Camera Profile DTO
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CameraProfile(BaseModel):
    id: int
    name: str
    camera_id: str
    dvr_connection_string: str
    rtsp_url: Optional[str] = None
    status: str  # 'active' | 'inactive' | 'error'
    rois: List['ROI'] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### ROI DTO
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Point(BaseModel):
    x: float
    y: float

class ROI(BaseModel):
    id: int
    camera_profile_id: int
    name: str
    polygon_coordinates: List[Point]
    color: str
    is_active: bool
    events: List['ROIEvent'] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### ROI Event DTO
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ROIEvent(BaseModel):
    id: int
    roi_id: int
    event_type_id: int
    start_time: str  # HH:mm format
    end_time: str    # HH:mm format
    days_of_week: List[int]  # [1,2,3,4,5] for Mon-Fri
    is_active: bool
    voice_alert_path: Optional[str] = None
    event_type: 'EventType'

    class Config:
        from_attributes = True
```

## 4. API Specifications

### 4.1 Camera Profile APIs

#### GET /api/camera-profiles
```python
# FastAPI Response Model
from pydantic import BaseModel
from typing import List

class GetCameraProfilesResponse(BaseModel):
    profiles: List[CameraProfile]
    total: int

# API Endpoint
@app.get("/api/camera-profiles", response_model=GetCameraProfilesResponse)
async def get_camera_profiles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    profiles = await camera_service.get_profiles(db, skip=skip, limit=limit)
    total = await camera_service.count_profiles(db)
    return GetCameraProfilesResponse(profiles=profiles, total=total)
```

#### POST /api/camera-profiles
```python
# Request Model
class CreateCameraProfileRequest(BaseModel):
    name: str
    camera_id: str
    dvr_connection_string: str
    rtsp_url: Optional[str] = None

# Response Model
class CreateCameraProfileResponse(BaseModel):
    profile: CameraProfile

# API Endpoint
@app.post("/api/camera-profiles", response_model=CreateCameraProfileResponse)
async def create_camera_profile(
    profile_data: CreateCameraProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = await camera_service.create_profile(db, profile_data, current_user.id)
    return CreateCameraProfileResponse(profile=profile)
```

#### PUT /api/camera-profiles/{profile_id}
```python
# Request Model
class UpdateCameraProfileRequest(BaseModel):
    name: Optional[str] = None
    dvr_connection_string: Optional[str] = None
    rtsp_url: Optional[str] = None
    status: Optional[str] = None  # 'active' | 'inactive' | 'error'

# API Endpoint
@app.put("/api/camera-profiles/{profile_id}", response_model=CameraProfile)
async def update_camera_profile(
    profile_id: int,
    profile_data: UpdateCameraProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await camera_service.update_profile(db, profile_id, profile_data)
```

#### DELETE /api/camera-profiles/{profile_id}
```python
@app.delete("/api/camera-profiles/{profile_id}")
async def delete_camera_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await camera_service.delete_profile(db, profile_id)
    return {"message": "Camera profile deleted successfully"}
```

### 4.2 ROI APIs

#### GET /api/camera-profiles/{profile_id}/rois
```python
@app.get("/api/camera-profiles/{profile_id}/rois", response_model=List[ROI])
async def get_camera_rois(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await roi_service.get_rois_by_camera(db, profile_id)
```

#### POST /api/camera-profiles/{profile_id}/rois
```python
# Request Model
class CreateROIRequest(BaseModel):
    name: str
    polygon_coordinates: List[Point]
    color: Optional[str] = "#FF0000"

@app.post("/api/camera-profiles/{profile_id}/rois", response_model=ROI)
async def create_roi(
    profile_id: int,
    roi_data: CreateROIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await roi_service.create_roi(db, roi_data, profile_id, current_user.id)
```

#### PUT /api/rois/{roi_id}
```python
class UpdateROIRequest(BaseModel):
    name: Optional[str] = None
    polygon_coordinates: Optional[List[Point]] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

@app.put("/api/rois/{roi_id}", response_model=ROI)
async def update_roi(
    roi_id: int,
    roi_data: UpdateROIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await roi_service.update_roi(db, roi_id, roi_data)
```

#### DELETE /api/rois/{roi_id}
```python
@app.delete("/api/rois/{roi_id}")
async def delete_roi(
    roi_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await roi_service.delete_roi(db, roi_id)
    return {"message": "ROI deleted successfully"}
```

### 4.3 ROI Event APIs

#### GET /api/rois/{roi_id}/events
```python
@app.get("/api/rois/{roi_id}/events", response_model=List[ROIEvent])
async def get_roi_events(
    roi_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await roi_event_service.get_events_by_roi(db, roi_id)
```

#### POST /api/rois/{roi_id}/events
```python
# Request Model
class CreateROIEventRequest(BaseModel):
    event_type_id: int
    start_time: str  # HH:mm format
    end_time: str    # HH:mm format
    days_of_week: List[int]  # [1,2,3,4,5] for Mon-Fri
    voice_alert_path: Optional[str] = None

@app.post("/api/rois/{roi_id}/events", response_model=ROIEvent)
async def create_roi_event(
    roi_id: int,
    event_data: CreateROIEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await roi_event_service.create_event(db, event_data, roi_id, current_user.id)
```

#### PUT /api/roi-events/{event_id}
```python
class UpdateROIEventRequest(BaseModel):
    event_type_id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    is_active: Optional[bool] = None
    voice_alert_path: Optional[str] = None

@app.put("/api/roi-events/{event_id}", response_model=ROIEvent)
async def update_roi_event(
    event_id: int,
    event_data: UpdateROIEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await roi_event_service.update_event(db, event_id, event_data)
```

#### DELETE /api/roi-events/{event_id}
```python
@app.delete("/api/roi-events/{event_id}")
async def delete_roi_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await roi_event_service.delete_event(db, event_id)
    return {"message": "ROI event deleted successfully"}
```

### 4.4 Event Type APIs

#### GET /api/event-types
```python
@app.get("/api/event-types", response_model=List[EventType])
async def get_event_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await event_type_service.get_all_event_types(db)
```

#### POST /api/event-types
```python
class CreateEventTypeRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    severity: str = "medium"
    default_voice_alert_path: Optional[str] = None
    default_color: str = "#FF0000"
    detection_algorithm: Optional[str] = None
    algorithm_parameters: Optional[Dict] = None

@app.post("/api/event-types", response_model=EventType)
async def create_event_type(
    event_type_data: CreateEventTypeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await event_type_service.create_event_type(db, event_type_data, current_user.id)
```

#### PUT /api/event-types/{event_type_id}
```python
@app.put("/api/event-types/{event_type_id}", response_model=EventType)
async def update_event_type(
    event_type_id: int,
    event_type_data: UpdateEventTypeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await event_type_service.update_event_type(db, event_type_id, event_type_data)
```

#### DELETE /api/event-types/{event_type_id}
```python
@app.delete("/api/event-types/{event_type_id}")
async def delete_event_type(
    event_type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await event_type_service.delete_event_type(db, event_type_id)
    return {"message": "Event type deleted successfully"}
```

### 4.5 Event Logs APIs

#### GET /api/event-logs
```python
from typing import Optional
from datetime import datetime

class GetEventLogsQuery(BaseModel):
    roi_id: Optional[int] = None
    event_type_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    limit: int = 100

@app.get("/api/event-logs", response_model=List[EventLog])
async def get_event_logs(
    roi_id: Optional[int] = Query(None),
    event_type_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await event_log_service.get_event_logs(
        db, roi_id, event_type_id, start_date, end_date, page, limit
    )
```

## 5. Frontend Components

### 5.1 Component Hierarchy
```
App
├── Header
├── Sidebar
├── CameraProfileList
│   ├── CameraProfileCard
│   └── AddProfileButton
├── CameraProfileDetail
│   ├── VideoStream
│   ├── ROICanvas
│   │   ├── PolygonDrawer
│   │   └── ROIDisplay
│   ├── ROIList
│   │   ├── ROIItem
│   │   └── AddROIButton
│   └── EventList
│       ├── EventItem
│       └── AddEventButton
├── EventLogs
│   ├── LogTable
│   └── LogFilters
└── Settings
    ├── EventTypeManager
    └── SystemConfiguration
```

### 5.2 Key Components

#### ROICanvas Component
```typescript
interface ROICanvasProps {
  videoStream: HTMLVideoElement;
  rois: ROI[];
  onROICreate: (coordinates: Point[]) => void;
  onROIUpdate: (roiId: number, coordinates: Point[]) => void;
  onROIDelete: (roiId: number) => void;
  mode: 'view' | 'draw' | 'edit';
}
```

#### VideoStream Component
```typescript
interface VideoStreamProps {
  rtspUrl: string;
  onFrame: (frame: ImageData) => void;
  isActive: boolean;
}
```

#### EventScheduler Component
```typescript
interface EventSchedulerProps {
  roiId: number;
  events: ROIEvent[];
  eventTypes: EventType[];
  onEventCreate: (event: CreateROIEventRequest) => void;
  onEventUpdate: (eventId: number, event: Partial<ROIEvent>) => void;
  onEventDelete: (eventId: number) => void;
}
```

## 6. Backend Services

### 6.1 Service Layer Architecture

#### Camera Service
```python
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import cv2
import asyncio

class CameraService:
    async def create_profile(
        self, 
        db: AsyncSession, 
        profile_data: CreateCameraProfileRequest, 
        user_id: int
    ) -> CameraProfile:
        """Create a new camera profile"""
        pass
    
    async def get_profile(self, db: AsyncSession, profile_id: int) -> Optional[CameraProfile]:
        """Get camera profile by ID"""
        pass
    
    async def get_profiles(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[CameraProfile]:
        """Get all camera profiles with pagination"""
        pass
    
    async def update_profile(
        self, 
        db: AsyncSession, 
        profile_id: int, 
        update_data: UpdateCameraProfileRequest
    ) -> CameraProfile:
        """Update camera profile"""
        pass
    
    async def delete_profile(self, db: AsyncSession, profile_id: int) -> None:
        """Delete camera profile"""
        pass
    
    async def connect_to_dvr(self, connection_string: str) -> bool:
        """Test connection to DVR"""
        pass
    
    async def get_video_stream(self, camera_id: str) -> cv2.VideoCapture:
        """Get OpenCV video stream for camera"""
        pass
```

#### ROI Service
```python
import cv2
import numpy as np
from shapely.geometry import Polygon

class ROIService:
    async def create_roi(
        self, 
        db: AsyncSession, 
        roi_data: CreateROIRequest, 
        camera_profile_id: int, 
        user_id: int
    ) -> ROI:
        """Create new ROI with polygon validation"""
        pass
    
    async def get_rois_by_camera(
        self, 
        db: AsyncSession, 
        camera_profile_id: int
    ) -> List[ROI]:
        """Get all ROIs for a camera"""
        pass
    
    async def update_roi(
        self, 
        db: AsyncSession, 
        roi_id: int, 
        update_data: UpdateROIRequest
    ) -> ROI:
        """Update ROI"""
        pass
    
    async def delete_roi(self, db: AsyncSession, roi_id: int) -> None:
        """Delete ROI"""
        pass
    
    def validate_polygon(self, coordinates: List[Point]) -> bool:
        """Validate polygon coordinates"""
        try:
            if len(coordinates) < 3:
                return False
            
            # Check if polygon is valid using shapely
            polygon_points = [(p.x, p.y) for p in coordinates]
            polygon = Polygon(polygon_points)
            return polygon.is_valid
        except Exception:
            return False
    
    def point_in_polygon(self, point: Point, polygon_coords: List[Point]) -> bool:
        """Check if point is inside polygon using OpenCV"""
        pts = np.array([[p.x, p.y] for p in polygon_coords], np.int32)
        test_point = (int(point.x), int(point.y))
        return cv2.pointPolygonTest(pts, test_point, False) >= 0
```

#### YOLO Event Detection Service
```python
import torch
from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, time

class YOLOEventDetectionService:
    def __init__(self):
        # Initialize YOLO models
        self.yolo_v5 = YOLO('yolov5s.pt')  # For general object detection
        self.yolo_v11 = YOLO('yolov11n.pt')  # For specific event detection
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Event type to class mapping
        self.event_class_mapping = {
            'person': 0,
            'vehicle': 2,  # car
            'intrusion': 0,  # person in restricted area
            'loitering': 0,  # person detection
            'abandoned_object': 27,  # suitcase/bag
        }
    
    async def process_frame(
        self, 
        frame: np.ndarray, 
        rois: List[ROI], 
        roi_events: List[ROIEvent]
    ) -> List[DetectedEvent]:
        """Process video frame and detect events in ROIs"""
        detected_events = []
        
        # Run YOLO detection
        results = self.yolo_v5(frame, device=self.device)
        
        # Process each detection
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get detection info
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Create center point of detection
                    center_point = Point(x=(x1 + x2) / 2, y=(y1 + y2) / 2)
                    
                    # Check if detection is in any ROI
                    for roi in rois:
                        if self._is_point_in_roi(center_point, roi):
                            # Check if any ROI events are active for this detection
                            for roi_event in roi_events:
                                if roi_event.roi_id == roi.id:
                                    if await self._check_event_timing(roi_event):
                                        detected_event = DetectedEvent(
                                            roi_id=roi.id,
                                            event_type_id=roi_event.event_type_id,
                                            confidence_score=float(confidence),
                                            bounding_box={
                                                'x1': float(x1), 'y1': float(y1),
                                                'x2': float(x2), 'y2': float(y2)
                                            },
                                            class_id=class_id,
                                            detected_at=datetime.now()
                                        )
                                        detected_events.append(detected_event)
        
        return detected_events
    
    def _is_point_in_roi(self, point: Point, roi: ROI) -> bool:
        """Check if point is inside ROI polygon"""
        polygon_points = [(p.x, p.y) for p in roi.polygon_coordinates]
        pts = np.array(polygon_points, np.int32)
        test_point = (int(point.x), int(point.y))
        return cv2.pointPolygonTest(pts, test_point, False) >= 0
    
    async def _check_event_timing(self, roi_event: ROIEvent) -> bool:
        """Check if event should be active based on time schedule"""
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        # Check time range
        start_time = time.fromisoformat(roi_event.start_time)
        end_time = time.fromisoformat(roi_event.end_time)
        
        if not (start_time <= current_time <= end_time):
            return False
        
        # Check day of week
        if current_day not in roi_event.days_of_week:
            return False
        
        return True
    
    async def trigger_alert(self, event: DetectedEvent) -> None:
        """Trigger alert for detected event"""
        # This will be implemented in AlertService
        pass
    
    async def record_video_clip(
        self, 
        camera_id: str, 
        duration: int = 30,
        output_path: str = None
    ) -> str:
        """Record video clip from camera"""
        # Implementation for video recording
        pass
```

#### Alert Service
```python
import asyncio
import pygame  # For audio playback
from pathlib import Path
from typing import List

class AlertService:
    def __init__(self):
        pygame.mixer.init()
        self.alert_queue = asyncio.Queue()
        self.processing = False
    
    async def send_voice_alert(self, alert_path: str, volume: float = 0.8) -> None:
        """Send voice alert"""
        try:
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.load(alert_path)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error playing voice alert: {e}")
    
    async def store_event_log(
        self, 
        db: AsyncSession, 
        event_log_data: CreateEventLogRequest
    ) -> EventLog:
        """Store event log in database"""
        # Implementation for database storage
        pass
    
    async def notify_clients(self, event: DetectedEvent) -> None:
        """Notify connected clients via WebSocket"""
        # Implementation for real-time notifications
        pass
    
    async def process_alert_queue(self) -> None:
        """Process queued alerts"""
        self.processing = True
        while self.processing:
            try:
                alert_data = await asyncio.wait_for(
                    self.alert_queue.get(), 
                    timeout=1.0
                )
                await self.send_voice_alert(alert_data['path'], alert_data['volume'])
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing alert: {e}")
```

### 6.2 Real-time Event Processing

#### Event Detection Pipeline
```python
import asyncio
import cv2
import numpy as np
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

class EventDetectionPipeline:
    def __init__(self):
        self.yolo_service = YOLOEventDetectionService()
        self.roi_service = ROIService()
        self.alert_service = AlertService()
        self.camera_service = CameraService()
        self.active_streams: Dict[str, cv2.VideoCapture] = {}
        self.processing = False
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def start_processing(self, camera_ids: List[str]) -> None:
        """Start processing video streams for multiple cameras"""
        self.processing = True
        
        # Start processing task for each camera
        tasks = []
        for camera_id in camera_ids:
            task = asyncio.create_task(self._process_camera_stream(camera_id))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def stop_processing(self) -> None:
        """Stop all video processing"""
        self.processing = False
        
        # Release all video streams
        for stream in self.active_streams.values():
            stream.release()
        self.active_streams.clear()
    
    async def _process_camera_stream(self, camera_id: str) -> None:
        """Process video stream for a single camera"""
        try:
            # Get video stream
            cap = await self.camera_service.get_video_stream(camera_id)
            self.active_streams[camera_id] = cap
            
            while self.processing:
                ret, frame = cap.read()
                if not ret:
                    # Try to reconnect
                    await asyncio.sleep(1)
                    continue
                
                # Process frame asynchronously
                await self._process_video_frame(camera_id, frame)
                
                # Control frame rate (30 FPS)
                await asyncio.sleep(1/30)
                
        except Exception as e:
            print(f"Error processing camera {camera_id}: {e}")
        finally:
            if camera_id in self.active_streams:
                self.active_streams[camera_id].release()
                del self.active_streams[camera_id]
    
    async def _process_video_frame(self, camera_id: str, frame: np.ndarray) -> None:
        """Process a single video frame"""
        try:
            # Get active ROIs and events for this camera (cached)
            rois = await self._get_active_rois(camera_id)
            if not rois:
                return
            
            roi_events = await self._get_active_roi_events([roi.id for roi in rois])
            
            # Process frame with YOLO
            detected_events = await self.yolo_service.process_frame(
                frame, rois, roi_events
            )
            
            # Handle detected events
            for event in detected_events:
                await self._handle_detected_event(camera_id, event, frame)
                
        except Exception as e:
            print(f"Error processing frame for camera {camera_id}: {e}")
    
    async def _handle_detected_event(
        self, 
        camera_id: str, 
        event: DetectedEvent, 
        frame: np.ndarray
    ) -> None:
        """Handle a detected event"""
        try:
            # Record video clip
            clip_path = await self.yolo_service.record_video_clip(
                camera_id, 
                duration=30
            )
            
            # Store event log
            event_log_data = CreateEventLogRequest(
                roi_id=event.roi_id,
                event_type_id=event.event_type_id,
                camera_profile_id=await self._get_camera_profile_id(camera_id),
                confidence_score=event.confidence_score,
                video_clip_path=clip_path,
                bounding_box=event.bounding_box,
                detection_metadata={'class_id': event.class_id}
            )
            
            await self.alert_service.store_event_log(None, event_log_data)
            
            # Trigger alert
            await self.yolo_service.trigger_alert(event)
            
            # Notify clients
            await self.alert_service.notify_clients(event)
            
        except Exception as e:
            print(f"Error handling detected event: {e}")
    
    async def _get_active_rois(self, camera_id: str) -> List[ROI]:
        """Get active ROIs for camera (with caching)"""
        # Implementation would include caching logic
        pass
    
    async def _get_active_roi_events(self, roi_ids: List[int]) -> List[ROIEvent]:
        """Get active ROI events (with caching)"""
        # Implementation would include caching logic
        pass
    
    async def _get_camera_profile_id(self, camera_id: str) -> int:
        """Get camera profile ID from camera_id"""
        # Implementation
        pass
```

## 7. Video Processing and Storage

### 7.1 Video Stream Processing
- **Input**: RTSP streams from DVR
- **Processing**: Real-time frame extraction and analysis
- **Output**: Event-triggered video clips

### 7.2 Storage Strategy
```
/video-storage/
├── /clips/
│   ├── /2024/
│   │   ├── /01/
│   │   │   ├── /camera_01/
│   │   │   │   ├── event_001_20240115_143022.mp4
│   │   │   │   └── event_002_20240115_151045.mp4
│   │   │   └── /camera_02/
│   │   └── /02/
├── /thumbnails/
│   └── /2024/01/...
└── /alerts/
    └── /voice/
        ├── intrusion_alert.mp3
        ├── loitering_alert.mp3
        └── custom_alert_001.mp3
```

### 7.3 Video Clip Management
```python
import cv2
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

class VideoClipManager:
    def __init__(self, storage_path: str = "/video-storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.active_recordings: Dict[str, cv2.VideoWriter] = {}
    
    async def record_clip(
        self, 
        camera_id: str, 
        event_id: int, 
        duration: int = 30,
        frame_source: cv2.VideoCapture = None
    ) -> str:
        """Record video clip for specified duration"""
        try:
            # Generate output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.storage_path / "clips" / datetime.now().strftime("%Y/%m")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{camera_id}_event_{event_id}_{timestamp}.mp4"
            output_path = output_dir / filename
            
            # Start recording
            if frame_source is None:
                frame_source = await self._get_camera_stream(camera_id)
            
            # Get video properties
            fps = frame_source.get(cv2.CAP_PROP_FPS)
            width = int(frame_source.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(frame_source.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                str(output_path), fourcc, fps, (width, height)
            )
            
            # Record frames
            frames_needed = int(fps * duration)
            frames_recorded = 0
            
            while frames_recorded < frames_needed:
                ret, frame = frame_source.read()
                if not ret:
                    break
                
                writer.write(frame)
                frames_recorded += 1
                
                # Small delay to maintain frame rate
                await asyncio.sleep(1/fps)
            
            writer.release()
            
            # Generate thumbnail
            await self.generate_thumbnail(str(output_path))
            
            return str(output_path)
            
        except Exception as e:
            print(f"Error recording clip: {e}")
            raise
    
    async def generate_thumbnail(self, video_path: str) -> str:
        """Generate thumbnail from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            
            if ret:
                # Get middle frame
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
                ret, frame = cap.read()
                
                if ret:
                    # Resize thumbnail
                    thumbnail = cv2.resize(frame, (320, 240))
                    
                    # Save thumbnail
                    thumbnail_path = video_path.replace('.mp4', '_thumb.jpg')
                    cv2.imwrite(thumbnail_path, thumbnail)
                    
                    cap.release()
                    return thumbnail_path
            
            cap.release()
            return ""
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return ""
    
    async def archive_old_clips(self, older_than_days: int = 30) -> int:
        """Archive or delete old video clips"""
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            archived_count = 0
            
            clips_dir = self.storage_path / "clips"
            
            for root, dirs, files in os.walk(clips_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        file_path = Path(root) / file
                        
                        # Get file modification time
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_time < cutoff_date:
                            # Move to archive or delete
                            archive_dir = self.storage_path / "archive" / file_time.strftime("%Y/%m")
                            archive_dir.mkdir(parents=True, exist_ok=True)
                            
                            archive_path = archive_dir / file
                            file_path.rename(archive_path)
                            archived_count += 1
            
            return archived_count
            
        except Exception as e:
            print(f"Error archiving clips: {e}")
            return 0
    
    async def get_clip_by_event(self, event_id: int) -> Optional[str]:
        """Get video clip path by event ID"""
        try:
            clips_dir = self.storage_path / "clips"
            
            for root, dirs, files in os.walk(clips_dir):
                for file in files:
                    if f"event_{event_id}_" in file and file.endswith('.mp4'):
                        return str(Path(root) / file)
            
            return None
            
        except Exception as e:
            print(f"Error finding clip: {e}")
            return None
    
    async def _get_camera_stream(self, camera_id: str) -> cv2.VideoCapture:
        """Get video stream for camera"""
        # Implementation would connect to camera
        pass
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        try:
            total_size = 0
            clip_count = 0
            
            clips_dir = self.storage_path / "clips"
            
            for root, dirs, files in os.walk(clips_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
                        clip_count += 1
            
            return {
                'total_size_gb': round(total_size / (1024**3), 2),
                'clip_count': clip_count,
                'storage_path': str(self.storage_path)
            }
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {'total_size_gb': 0, 'clip_count': 0, 'storage_path': str(self.storage_path)}
```

## 8. Alert System

### 8.1 Voice Alert Architecture
```python
import asyncio
import pygame
import threading
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertRequest:
    alert_path: str
    volume: float = 0.8
    priority: AlertPriority = AlertPriority.MEDIUM
    loop_count: int = 1
    delay: float = 0.0

class VoiceAlertSystem:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.alert_queue = asyncio.Queue()
        self.preloaded_sounds: Dict[str, pygame.mixer.Sound] = {}
        self.currently_playing = False
        self.processing = False
        self.alert_cooldowns: Dict[str, float] = {}
        self.cooldown_period = 5.0  # seconds
        
    async def play_alert(
        self, 
        alert_path: str, 
        volume: float = 0.8,
        priority: AlertPriority = AlertPriority.MEDIUM,
        loop_count: int = 1
    ) -> bool:
        """Play voice alert immediately"""
        try:
            # Check cooldown
            if not self._can_play_alert(alert_path):
                return False
            
            # Load sound if not preloaded
            if alert_path not in self.preloaded_sounds:
                sound = pygame.mixer.Sound(alert_path)
                self.preloaded_sounds[alert_path] = sound
            else:
                sound = self.preloaded_sounds[alert_path]
            
            # Set volume and play
            sound.set_volume(volume)
            
            for i in range(loop_count):
                sound.play()
                
                # Wait for sound to finish
                while pygame.mixer.get_busy():
                    await asyncio.sleep(0.1)
                
                # Small delay between loops
                if i < loop_count - 1:
                    await asyncio.sleep(0.5)
            
            # Update cooldown
            self.alert_cooldowns[alert_path] = asyncio.get_event_loop().time()
            
            return True
            
        except Exception as e:
            print(f"Error playing alert {alert_path}: {e}")
            return False
    
    async def schedule_alert(
        self, 
        alert_path: str, 
        delay: float,
        volume: float = 0.8,
        priority: AlertPriority = AlertPriority.MEDIUM
    ) -> None:
        """Schedule alert to play after delay"""
        alert_request = AlertRequest(
            alert_path=alert_path,
            volume=volume,
            priority=priority,
            delay=delay
        )
        
        # Schedule with delay
        asyncio.create_task(self._schedule_alert_with_delay(alert_request))
    
    async def _schedule_alert_with_delay(self, alert_request: AlertRequest) -> None:
        """Internal method to handle delayed alerts"""
        await asyncio.sleep(alert_request.delay)
        await self.queue_alert(alert_request)
    
    async def queue_alert(self, alert_request: AlertRequest) -> None:
        """Queue alert for processing"""
        await self.alert_queue.put(alert_request)
    
    async def stop_all_alerts(self) -> None:
        """Stop all currently playing alerts"""
        pygame.mixer.stop()
        self.currently_playing = False
    
    async def preload_alerts(self, alert_paths: List[str]) -> int:
        """Preload alert sounds for faster playback"""
        loaded_count = 0
        
        for alert_path in alert_paths:
            try:
                if Path(alert_path).exists():
                    sound = pygame.mixer.Sound(alert_path)
                    self.preloaded_sounds[alert_path] = sound
                    loaded_count += 1
            except Exception as e:
                print(f"Error preloading alert {alert_path}: {e}")
        
        return loaded_count
    
    async def start_processing(self) -> None:
        """Start the alert processing loop"""
        self.processing = True
        
        while self.processing:
            try:
                # Get alert from queue with timeout
                alert_request = await asyncio.wait_for(
                    self.alert_queue.get(), 
                    timeout=1.0
                )
                
                # Play the alert
                await self.play_alert(
                    alert_request.alert_path,
                    alert_request.volume,
                    alert_request.priority,
                    alert_request.loop_count
                )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing alert: {e}")
    
    async def stop_processing(self) -> None:
        """Stop the alert processing loop"""
        self.processing = False
        await self.stop_all_alerts()
    
    def _can_play_alert(self, alert_path: str) -> bool:
        """Check if alert can be played (cooldown check)"""
        current_time = asyncio.get_event_loop().time()
        
        if alert_path in self.alert_cooldowns:
            last_played = self.alert_cooldowns[alert_path]
            if current_time - last_played < self.cooldown_period:
                return False
        
        return True
    
    def get_loaded_alerts(self) -> List[str]:
        """Get list of preloaded alert paths"""
        return list(self.preloaded_sounds.keys())
    
    def unload_alert(self, alert_path: str) -> bool:
        """Unload alert from memory"""
        if alert_path in self.preloaded_sounds:
            del self.preloaded_sounds[alert_path]
            return True
        return False
    
    def set_cooldown_period(self, seconds: float) -> None:
        """Set cooldown period between same alerts"""
        self.cooldown_period = max(0, seconds)
    
    def get_queue_size(self) -> int:
        """Get current alert queue size"""
        return self.alert_queue.qsize()
```

### 8.2 Alert Types and Priorities
- **High Priority**: Intrusion, trespassing
- **Medium Priority**: Loitering, unusual activity
- **Low Priority**: System notifications

## 9. Security Considerations

### 9.1 Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Session management

### 9.2 Data Security
- Encrypted database connections
- Secure video stream transmission
- Access control for video clips
- Audit logging for all operations

### 9.3 Network Security
- HTTPS/WSS for all communications
- VPN support for remote DVR connections
- Firewall configuration recommendations
- Network segmentation

## 10. Performance and Scalability

### 10.1 Performance Optimization
- **Video Processing**: GPU acceleration with OpenCV
- **Database**: Indexing strategies for time-based queries
- **Caching**: Redis for frequently accessed data
- **Load Balancing**: Multiple backend instances

### 10.2 Scalability Considerations
- **Horizontal Scaling**: Multiple processing nodes
- **Database Sharding**: By camera or time
- **CDN Integration**: For video clip distribution
- **Microservices**: Separate services for different functions

## 11. Testing Strategy

### 11.1 Unit Testing
- Service layer testing
- Component testing
- Utility function testing
- Database operation testing

### 11.2 Integration Testing
- API endpoint testing
- Database integration
- Video stream processing
- Alert system testing

### 11.3 End-to-End Testing
- Full user workflows
- Multi-camera scenarios
- Event detection accuracy
- System performance under load

## 12. Deployment Architecture

### 12.1 Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/surveillance_dev
      - REDIS_URL=redis://redis:6379/0
      - YOLO_MODEL_PATH=/app/models
      - DEBUG=true
    volumes:
      - ./backend:/app
      - ./models:/app/models
      - ./video-storage:/app/video-storage
    depends_on:
      - postgres
      - redis
  
  celery:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/surveillance_dev
      - REDIS_URL=redis://redis:6379/0
      - YOLO_MODEL_PATH=/app/models
    volumes:
      - ./backend:/app
      - ./models:/app/models
      - ./video-storage:/app/video-storage
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: surveillance_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 12.2 Production Environment
- **Container Orchestration**: Kubernetes
- **Database**: Managed PostgreSQL service
- **File Storage**: AWS S3 or equivalent
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

## 13. Monitoring and Maintenance

### 13.1 System Monitoring
- **Metrics**: CPU, memory, disk usage
- **Application Metrics**: API response times, error rates
- **Business Metrics**: Event detection accuracy, alert frequency
- **Video Stream Health**: Connection status, quality metrics

### 13.2 Maintenance Procedures
- **Database Backups**: Daily automated backups
- **Log Rotation**: Prevent disk space issues
- **Software Updates**: Regular security patches
- **Performance Tuning**: Query optimization, index maintenance

## 14. Implementation Phases

### Phase 1: Core Infrastructure (4-6 weeks)
- Database schema implementation with PostgreSQL
- FastAPI backend setup with async SQLAlchemy
- React frontend framework setup
- Camera profile management APIs
- Docker development environment

### Phase 2: ROI and Event Management (3-4 weeks)
- Polygon drawing interface with Fabric.js/Konva.js
- ROI CRUD operations with OpenCV validation
- Event type management with YOLO integration
- Time-based scheduling system
- WebSocket real-time communication

### Phase 3: YOLO Video Processing and Detection (4-6 weeks)
- YOLOv5/v11 model integration
- Video stream processing with OpenCV
- Async frame processing pipeline
- Event detection in ROIs
- Basic voice alert system with pygame

### Phase 4: Advanced Features (3-4 weeks)
- Advanced voice alert system with queue management
- Video clip recording and storage
- Celery background task processing
- Real-time notifications via Socket.io
- Performance optimization with GPU acceleration

### Phase 5: Testing and Deployment (2-3 weeks)
- Comprehensive testing with pytest
- Production Kubernetes deployment
- API documentation with FastAPI Swagger
- User training materials

## 15. Risk Assessment and Mitigation

### 15.1 Technical Risks
- **Video Stream Reliability**: Implement reconnection logic
- **Performance Bottlenecks**: Load testing and optimization
- **Storage Capacity**: Implement archiving strategies
- **Network Latency**: Edge processing capabilities

### 15.2 Business Risks
- **False Positives**: Machine learning model tuning
- **System Downtime**: High availability architecture
- **Data Privacy**: Compliance with regulations
- **User Adoption**: Intuitive UI design

## 16. Conclusion

This software design document provides a comprehensive architecture for a surveillance system with ROI-based event detection and alerting. The modular design allows for incremental development and future enhancements while maintaining scalability and performance requirements.

The system addresses all key requirements:
- Multiple camera profiles with DVR integration
- Manual ROI definition with polygon drawing
- Time-based event scheduling
- Multi-ROI support per camera
- Voice alert system
- Video clip storage and management
- Comprehensive CRUD operations

The proposed technology stack and architecture ensure a robust, scalable, and maintainable solution that can be deployed in various environments from small installations to enterprise-scale deployments.
