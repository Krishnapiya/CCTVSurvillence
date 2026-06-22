import asyncio
import logging

from app.core.config import settings
from app.services.master_sync_agent import run_master_sync_cycle

logger = logging.getLogger("master_sync")
_sync_task: asyncio.Task | None = None


async def master_sync_loop() -> None:
    interval_secs = max(60, settings.SYNC_PUSH_INTERVAL_MINUTES * 60)
    logger.info(
        "Master sync loop started (every %s min) -> %s",
        settings.SYNC_PUSH_INTERVAL_MINUTES,
        settings.MASTER_API_URL,
    )
    while True:
        try:
            if settings.SYNC_ENABLED:
                result = await run_master_sync_cycle()
                logger.info("Master sync cycle complete: %s", result)
        except Exception as exc:
            logger.exception("Master sync loop error: %s", exc)
        await asyncio.sleep(interval_secs)


def start_master_sync_background() -> None:
    global _sync_task
    if not settings.SYNC_ENABLED:
        logger.info("Master sync disabled — set SYNC_ENABLED=true in .env to enable")
        return
    if _sync_task and not _sync_task.done():
        return
    _sync_task = asyncio.create_task(master_sync_loop())


async def stop_master_sync_background() -> None:
    global _sync_task
    if _sync_task and not _sync_task.done():
        _sync_task.cancel()
        try:
            await _sync_task
        except asyncio.CancelledError:
            pass
    _sync_task = None
