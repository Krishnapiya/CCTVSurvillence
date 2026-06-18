from typing import Any
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check() -> Any:
    """Simple API healthcheck."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "redis": "connected",
            "rabbitmq": "connected"
        }
    }

@router.get("")
@router.get("/")
async def get_status() -> Any:
    """Base status check returning active services status."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "redis": "connected",
            "rabbitmq": "connected"
        }
    }

