import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Surveillance Platform API"
    API_V1_STR: str = "/api/v1"
    
    # Database and Caching
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://surveillance_user:password@localhost:5432/surveillance_system"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="amqp://guest:guest@localhost:5672//")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    
    # Security
    JWT_SECRET: str = Field(default="supersecretjwtkey123!@#")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Media Storage and AI weights
    MEDIA_STORAGE_DIR: str = Field(default="./media")
    MODEL_WEIGHTS_DIR: str = Field(default="./models")
    
    # Model Weights Specific Configuration
    # Custom fire/smoke detection model weights
    YOLO_CUSTOM_FIRE_SMOKE_PATH: str = Field(
        default="/media/ai/1646F35346F3325B/survialance/yolo/backend/models/best.pt"
    )
    YOLO_PRETRAINED_DETECTION_PATH: str = Field(default="yolo11s.pt")
    
    # Qwen-VL Config
    # If a GPU is not available, we can mock or call Qwen via HuggingFace/ollama/API
    QWEN_VL_MODEL_ID: str = Field(default="Qwen/Qwen2.5-VL-2B-Instruct")
    USE_LOCAL_LLM: bool = Field(default=False)  # Set to true to attempt local GPU loading
    
    # Event Config
    PRE_TRIGGER_DURATION_SECS: float = 5.0
    POST_TRIGGER_DURATION_SECS: float = 5.0

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
os.makedirs(settings.MEDIA_STORAGE_DIR, exist_ok=True)
os.makedirs(settings.MODEL_WEIGHTS_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_STORAGE_DIR, "snapshots"), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_STORAGE_DIR, "clips"), exist_ok=True)
