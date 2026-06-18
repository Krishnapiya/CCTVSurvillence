from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.alert import AlertRepository
from app.models.alert import Alert
from app.models.audit import AuditLog
from app.services.websocket_manager import ws_manager

class AlertManager:
    async def acknowledge_alert(self, alert_id: UUID, user_id: UUID, db: AsyncSession) -> Optional[Alert]:
        repo = AlertRepository(db)
        alert = await repo.get_with_relations(alert_id)
        if not alert:
            return None

        # Transition status
        alert = await repo.update(alert, {
            "status": "ACKNOWLEDGED",
            "assigned_to": user_id
        })

        # Write audit log
        audit = AuditLog(
            user_id=user_id,
            action="ALERT_ACKNOWLEDGED",
            target_table="alerts",
            target_id=alert_id,
            details={"previous_status": "CREATED", "new_status": "ACKNOWLEDGED"}
        )
        db.add(audit)
        await db.flush()

        # WS Broadcast
        await ws_manager.broadcast({
            "msg_type": "alert_update",
            "alert": {
                "id": str(alert.id),
                "status": "ACKNOWLEDGED",
                "assigned_to": str(user_id)
            }
        })
        
        return alert

    async def resolve_alert(self, alert_id: UUID, user_id: UUID, db: AsyncSession) -> Optional[Alert]:
        repo = AlertRepository(db)
        alert = await repo.get_with_relations(alert_id)
        if not alert:
            return None

        # Transition status
        alert = await repo.update(alert, {
            "status": "RESOLVED",
            "resolved_at": datetime.now(timezone.utc)
        })

        # Write audit log
        audit = AuditLog(
            user_id=user_id,
            action="ALERT_RESOLVED",
            target_table="alerts",
            target_id=alert_id,
            details={"previous_status": alert.status, "new_status": "RESOLVED"}
        )
        db.add(audit)
        await db.flush()

        # WS Broadcast
        await ws_manager.broadcast({
            "msg_type": "alert_update",
            "alert": {
                "id": str(alert.id),
                "status": "RESOLVED",
                "resolved_at": alert.resolved_at.isoformat()
            }
        })
        
        return alert

alert_manager = AlertManager()
