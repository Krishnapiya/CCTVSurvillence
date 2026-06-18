# Backend Architecture Overview - Surveillance System

## 1. Executive Summary

The backend of our surveillance system is built using Python with FastAPI as the web framework, designed to handle real-time video processing, AI-based event detection, and alert management. The architecture follows an event-driven, asynchronous pattern that can efficiently process multiple camera feeds simultaneously while maintaining low latency for alert generation.

## 2. Core Architecture Components

### 2.1 Web Framework Layer (FastAPI)

**Purpose**: Provides the HTTP API interface for the frontend and external systems.

**Key Responsibilities**:
- Exposes RESTful endpoints for camera management, ROI configuration, and event handling
- Handles authentication and authorization using JWT tokens
- Provides automatic API documentation through OpenAPI/Swagger
- Manages request validation using Pydantic models
- Supports WebSocket connections for real-time updates

**Why FastAPI**: Chosen for its native async support, automatic validation, and excellent performance characteristics. It allows us to handle many concurrent connections efficiently, which is crucial for a surveillance system monitoring multiple cameras.

### 2.2 Database Layer (Async SQLAlchemy + PostgreSQL)

**Purpose**: Persistent storage for all system data including camera configurations, ROIs, events, and logs.

**Key Components**:
- **Async SQLAlchemy**: Provides asynchronous database operations, preventing the database from becoming a bottleneck
- **PostgreSQL**: Robust relational database with excellent support for JSON data types (perfect for storing polygon coordinates)
- **Connection Pooling**: Manages database connections efficiently to handle high load
- **Migration Support**: Alembic for database schema versioning

**Data Organization**:
- Users and authentication data
- Camera profiles with connection details
- ROI definitions with polygon coordinates
- Event types and scheduling information
- Event logs and alert history
- System configuration and audit trails

### 2.3 AI/ML Processing Layer (YOLO + OpenCV)

**Purpose**: Real-time object detection and event recognition within defined regions of interest.

**YOLO Models**:
- **YOLOv5**: Used for general object detection (people, vehicles, etc.)
- **YOLOv11**: Used for specialized event detection with higher accuracy
- **GPU Acceleration**: Leverages CUDA when available for faster processing
- **Model Loading**: Models are loaded once at startup and cached for efficiency

**OpenCV Integration**:
- **Video Stream Handling**: Connects to RTSP streams from DVR systems
- **Frame Processing**: Extracts and processes individual frames from video streams
- **Polygon Operations**: Determines if detected objects fall within ROI boundaries
- **Video Recording**: Captures video clips when events are detected

**Processing Pipeline**:
1. Capture frame from video stream
2. Run YOLO detection on the frame
3. Filter detections based on confidence thresholds
4. Check if detection centers fall within active ROIs
5. Verify event timing constraints
6. Generate alerts if all conditions are met

### 2.4 Event Detection Engine

**Purpose**: Coordinates the AI processing with business logic to determine when events should trigger alerts.

**Core Logic**:
- **Time-based Scheduling**: Events only trigger during specified time windows and days
- **ROI Matching**: Ensures detections occur within defined polygon areas
- **Confidence Filtering**: Ignores low-confidence detections to reduce false positives
- **Cooldown Management**: Prevents alert spam by enforcing minimum intervals between similar alerts

**Event Types Supported**:
- **Intrusion Detection**: Person detected in restricted area
- **Loitering**: Person remaining in area for extended period
- **Vehicle Detection**: Unauthorized vehicles in monitored zones
- **Abandoned Objects**: Objects left unattended in sensitive areas
- **Custom Events**: User-defined detection scenarios

### 2.5 Alert Management System

**Purpose**: Handles the generation, queuing, and delivery of alerts when events are detected.

**Alert Types**:
- **Voice Alerts**: Pre-recorded audio messages played through speakers
- **Visual Notifications**: Real-time updates sent to frontend via WebSocket
- **Email Alerts**: Optional email notifications for high-priority events
- **SMS Alerts**: Text message alerts for critical events

**Alert Processing**:
- **Priority Queuing**: High-priority alerts are processed first
- **Cooldown Management**: Prevents alert fatigue from repeated triggers
- **Sound Management**: Preloads audio files for faster response times
- **Volume Control**: Adjustable alert volumes based on time of day or event severity

### 2.6 Background Task Processing (Celery)

**Purpose**: Handles long-running tasks asynchronously to prevent blocking the main API responses.

**Task Types**:
- **Video Clip Processing**: Recording and encoding video clips
- **Thumbnail Generation**: Creating preview images from video
- **File Cleanup**: Archiving old video files and managing storage
- **Report Generation**: Creating daily/weekly activity reports
- **System Maintenance**: Database cleanup and optimization

**Celery Configuration**:
- **Redis Broker**: Fast message broker for task distribution
- **Worker Processes**: Multiple worker processes handle tasks in parallel
- **Task Priorities**: Critical tasks (like alert processing) get higher priority
- **Error Handling**: Automatic retry for failed tasks with exponential backoff

### 2.7 Real-time Communication (WebSocket)

**Purpose**: Provides instant updates to connected frontend clients when events occur.

**WebSocket Features**:
- **Live Event Notifications**: Real-time alerts sent to all connected users
- **System Status Updates**: Camera connection status and health information
- **Configuration Changes**: Live updates when ROIs or events are modified
- **User Presence**: Track which users are currently viewing the system

**Message Types**:
- Event detection notifications
- Camera status changes
- System health alerts
- User activity updates

## 3. Data Flow Architecture

### 3.1 Video Processing Flow

1. **Stream Acquisition**: Backend connects to RTSP streams from DVR systems
2. **Frame Extraction**: Continuous extraction of video frames at configurable FPS
3. **AI Processing**: Each frame is analyzed by YOLO models for object detection
4. **ROI Filtering**: Detections are filtered based on polygon boundaries
5. **Event Validation**: Time-based and confidence-based validation
6. **Alert Generation**: If all conditions are met, alerts are triggered
7. **Storage**: Event logs and video clips are stored for later review

### 3.2 API Request Flow

1. **Request Reception**: FastAPI receives HTTP requests from frontend
2. **Authentication**: JWT tokens are validated for secure access
3. **Request Validation**: Pydantic models validate and sanitize input data
4. **Business Logic**: Service layer processes the request according to business rules
5. **Database Operations**: Async SQLAlchemy handles database interactions
6. **Response Generation**: Results are formatted and returned as JSON
7. **WebSocket Updates**: Relevant changes are broadcast to connected clients

### 3.3 Alert Processing Flow

1. **Event Detection**: AI system detects potential event in video frame
2. **Validation**: Event is validated against ROI, time, and confidence rules
3. **Alert Creation**: Alert request is created and queued for processing
4. **Priority Assignment**: Alert priority is determined based on event type
5. **Delivery**: Alert is delivered through appropriate channels (voice, visual, etc.)
6. **Logging**: All alert activities are logged for audit and analysis

## 4. Service Layer Architecture

### 4.1 Camera Service

**Responsibilities**:
- Managing camera profile CRUD operations
- Testing and maintaining DVR connections
- Handling video stream initialization and reconnection
- Monitoring camera health and status

**Key Features**:
- Automatic stream reconnection on failure
- Connection health monitoring with periodic checks
- Stream quality assessment and reporting
- Support for multiple DVR protocols and formats

### 4.2 ROI Service

**Responsibilities**:
- Creating and managing polygon-based regions of interest
- Validating polygon coordinates for geometric correctness
- Calculating ROI properties (area, centroid, etc.)
- Point-in-polygon calculations for detection filtering

**Geometric Processing**:
- Uses Shapely library for advanced geometric operations
- Validates polygon self-intersection and closure
- Calculates optimal point placement for detection accuracy
- Supports complex polygon shapes with multiple vertices

### 4.3 Event Detection Service

**Responsibilities**:
- Coordinating YOLO model processing
- Managing detection confidence thresholds
- Implementing time-based event scheduling
- Handling event cooldown and rate limiting

**Detection Logic**:
- Multi-model processing for improved accuracy
- Ensemble methods for reducing false positives
- Adaptive thresholding based on environmental conditions
- Learning algorithms for improving detection over time

### 4.4 Alert Service

**Responsibilities**:
- Managing alert queue and processing
- Handling voice alert playback with pygame
- Coordinating multi-channel alert delivery
- Managing alert cooldown and priority systems

**Alert Management**:
- Intelligent alert prioritization based on event severity
- Adaptive volume control based on ambient noise levels
- Alert escalation procedures for unacknowledged events
- Integration with external alert systems (email, SMS, etc.)

### 4.5 Video Management Service

**Responsibilities**:
- Recording video clips when events are detected
- Generating thumbnails for video previews
- Managing video file storage and archiving
- Handling video compression and format conversion

**Storage Management**:
- Automatic archiving of old video files
- Storage space monitoring and cleanup
- Video compression for efficient storage
- Cloud storage integration for backup and redundancy

## 5. Security Architecture

### 5.1 Authentication & Authorization

**JWT Token System**:
- Stateless authentication using JSON Web Tokens
- Token expiration and refresh mechanisms
- Role-based access control (admin, operator, viewer)
- Secure token storage and transmission

**Permission Model**:
- Hierarchical user roles with different privilege levels
- Resource-based access control for cameras and ROIs
- Audit logging for all user actions
- Session management and monitoring

### 5.2 Data Security

**Database Security**:
- Encrypted database connections using SSL/TLS
- Sensitive data encryption at rest
- SQL injection prevention through parameterized queries
- Regular database access auditing

**API Security**:
- Rate limiting to prevent abuse
- CORS configuration for secure cross-origin requests
- Input validation and sanitization
- Protection against common web vulnerabilities

### 5.3 Network Security

**Secure Communications**:
- HTTPS/WSS for all client-server communications
- VPN support for secure remote DVR connections
- Firewall configuration recommendations
- Network segmentation for surveillance infrastructure

## 6. Performance and Scalability

### 6.1 Performance Optimization

**Async Processing**:
- Non-blocking I/O operations throughout the application
- Concurrent processing of multiple video streams
- Efficient database connection pooling
- Optimized memory usage for video frame processing

**Caching Strategy**:
- Redis caching for frequently accessed data
- Model and configuration caching in memory
- Database query result caching
- Static asset caching for improved response times

### 6.2 Scalability Considerations

**Horizontal Scaling**:
- Multiple backend instances behind load balancer
- Distributed task processing with Celery workers
- Database read replicas for improved query performance
- Microservices architecture for future expansion

**Resource Management**:
- GPU acceleration for AI processing
- Memory-efficient video frame handling
- Storage optimization for video clips
- Network bandwidth management for multiple streams

## 7. Monitoring and Maintenance

### 7.1 System Monitoring

**Health Monitoring**:
- Camera connection status monitoring
- AI model performance tracking
- Database performance metrics
- System resource utilization monitoring

**Alert Monitoring**:
- Alert delivery success rates
- False positive rate tracking
- System response time monitoring
- User activity and engagement metrics

### 7.2 Maintenance Procedures

**Automated Maintenance**:
- Database backup and cleanup procedures
- Video file archiving and storage management
- System log rotation and analysis
- Performance optimization routines

**Manual Maintenance**:
- Model retraining and updates
- System configuration updates
- Security patch management
- Performance tuning and optimization

## 8. Integration Points

### 8.1 External System Integration

**DVR Integration**:
- Support for multiple DVR manufacturers
- RTSP and HTTP streaming protocols
- ONVIF compliance for standardization
- Custom protocol adapters for proprietary systems

**Third-party Services**:
- Cloud storage integration (AWS S3, Azure Blob)
- Email service integration (SMTP, SendGrid)
- SMS service integration (Twilio, etc.)
- Push notification services

### 8.2 API Integration

**REST API**:
- Comprehensive RESTful API for all system functions
- OpenAPI documentation for easy integration
- Webhook support for event notifications
- Third-party authentication support (OAuth, SAML)

**WebSocket API**:
- Real-time event streaming
- Live video feed access
- System status updates
- Collaborative features for multiple users

## 9. Deployment Architecture

### 9.1 Container-based Deployment

**Docker Containers**:
- Containerized application components
- Consistent deployment across environments
- Easy scaling and management
- Isolation of dependencies and services

**Orchestration**:
- Kubernetes for production deployment
- Docker Compose for development environments
- Service discovery and load balancing
- Automated scaling and healing

### 9.2 Environment Management

**Development Environment**:
- Local development setup with Docker Compose
- Hot reloading for rapid development
- Debug tools and logging configuration
- Test database and mock services

**Production Environment**:
- High-availability deployment with redundancy
- Load balancing and auto-scaling
- Monitoring and alerting systems
- Backup and disaster recovery procedures

## 10. Technology Rationale

### 10.1 Python Ecosystem Benefits

**Rich AI/ML Libraries**:
- PyTorch for deep learning models
- OpenCV for computer vision operations
- NumPy for efficient numerical computations
- Scikit-learn for additional ML algorithms

**Web Framework Advantages**:
- FastAPI's async support for high concurrency
- Automatic API documentation generation
- Type hints for better code quality
- Excellent performance characteristics

**Ecosystem Integration**:
- Extensive third-party library support
- Strong community and documentation
- Easy integration with cloud services
- Proven track record in production systems

### 10.2 YOLO Model Selection

**YOLOv5 Advantages**:
- Proven reliability in production environments
- Good balance of speed and accuracy
- Extensive community support and documentation
- Easy deployment and optimization

**YOLOv11 Advantages**:
- Latest architecture with improved accuracy
- Better performance on specific object types
- Enhanced feature extraction capabilities
- Optimized for edge deployment

**Dual Model Strategy**:
- General detection with YOLOv5 for reliability
- Specialized detection with YOLOv11 for accuracy
- Model ensemble for improved overall performance
- Flexible model selection based on use case

## 11. Future Enhancements

### 11.1 AI/ML Improvements

**Advanced Detection**:
- Custom model training for specific environments
- Behavioral analysis for anomaly detection
- Face recognition and person tracking
- Vehicle license plate recognition

**Learning Systems**:
- Adaptive thresholding based on environment
- False positive reduction through learning
- User feedback integration for model improvement
- Automated model retraining and updates

### 11.2 System Enhancements

**Advanced Features**:
- Multi-camera tracking and correlation
- 3D scene reconstruction
- Predictive analytics for threat assessment
- Integration with physical security systems

**Performance Improvements**:
- Edge processing for reduced latency
- Distributed AI processing across multiple nodes
- Real-time analytics dashboard
- Advanced compression and streaming optimization

## 12. Conclusion

The backend architecture provides a robust, scalable foundation for the surveillance system that can handle real-time video processing, AI-based event detection, and comprehensive alert management. The Python-based technology stack offers excellent AI/ML capabilities, while the async architecture ensures high performance and scalability.

The modular design allows for easy maintenance and future enhancements, while the comprehensive security and monitoring features ensure reliable operation in production environments. The system is designed to grow with the needs of the organization, supporting everything from single-camera installations to large-scale enterprise deployments.
