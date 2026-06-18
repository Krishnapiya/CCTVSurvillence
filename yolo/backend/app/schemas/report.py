from typing import Dict, Any, List
from pydantic import BaseModel

class SeveritySummary(BaseModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0

class StatusSummary(BaseModel):
    CREATED: int = 0
    ACKNOWLEDGED: int = 0
    RESOLVED: int = 0

class ReportsSummaryResponse(BaseModel):
    total_alerts: int
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    by_event_type: Dict[str, int]
    camera_status_counts: Dict[str, int]
