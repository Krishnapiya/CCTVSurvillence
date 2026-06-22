import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    MODELS_DIR: Path = BASE_DIR / "models"
    EVENTS_DIR: Path = BASE_DIR / "events"
    VIDEOS_DIR: Path = BASE_DIR / "videos"

    # Ensure directories exist
    def create_dirs(self):
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # YOLO Model Settings
    YOLO_MODEL_NAME: str = "yolo11m-pose.pt"
    @property
    def YOLO_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / self.YOLO_MODEL_NAME)
    
    DETECTION_CONFIDENCE: float = 0.20
    POSE_KEYPOINT_CONFIDENCE: float = 0.20

    # Fall and Posture Analysis Thresholds
    # Angle in degrees relative to the vertical line
    FALL_ANGLE_THRESHOLD: float = 60.0  # Horizontal if torso angle > 60 degrees
    VERTICAL_ANGLE_THRESHOLD: float = 30.0 # Vertical if torso angle < 30 degrees
    
    # Fall state machine window (seconds)
    FALL_TRANSITION_WINDOW: float = 10.0 # Must transition from VERTICAL -> FALLING -> HORIZONTAL in 10 seconds

    # Motionless Verification
    MOTION_THRESHOLD: float = 12.0 # Keypoint pixel standard deviation limit to classify as motionless
    MOTIONLESS_TIME_THRESHOLD: float = 3.0 # Seconds a person must remain motionless in horizontal posture
    
    # Velocity Analysis
    RAPID_FALL_VELOCITY_THRESHOLD: float = 40.0 # Pixel speed downwards (pixels per second) to qualify as a rapid fall

    # Alert Settings
    ALERT_COOLDOWN: float = 30.0 # Seconds to wait before generating another alert for the same person
    SOUND_ALARM_ENABLED: bool = True
    ALARM_SOUND_PATH: str = "/usr/share/sounds/alsa/Front_Center.wav" # Default sound on many Linux distros

    # PostgreSQL Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "fall_detection")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")

    # Camera/Video Source
    # 0 for webcam, or path to local mp4/avi file, or rtsp:// url
    VIDEO_SOURCE: str = os.getenv("VIDEO_SOURCE", "rtsp://swguser:Swguser789@@192.168.50.135:554/Streaming/Channels/101")
    VIDEO_SOURCE_TIMESTAMP: float = 0.0
    
    # Video Clip Recording
    SAVE_VIDEO_ENABLED: bool = False
    RECORDING_FPS: int = 15
    PRE_EVENT_BUFFER_DURATION: int = 10 # Seconds of video buffer to save before the fall event
    POST_EVENT_BUFFER_DURATION: int = 5 # Seconds of video to save after the fall event
    EVENT_RECORDING_DURATION: int = 40 # Total recording duration in seconds (40 seconds)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate settings
settings = Settings()
settings.create_dirs()
