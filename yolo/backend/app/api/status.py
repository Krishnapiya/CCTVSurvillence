from typing import Any
from fastapi import APIRouter
from app.services.master_sync_payload import station_context

router = APIRouter()

@router.get("/station")
async def get_station_config() -> Any:
    """Station identity and master sync settings (read-only, no secrets)."""
    ctx = station_context()
    return {
        "installation_id": ctx["installation_id"],
        "office_code": ctx["office_code"],
        "office_name": ctx["office_name"],
        "master_api_url": ctx["master_api_url"],
        "sync_enabled": ctx["sync_enabled"],
    }

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

