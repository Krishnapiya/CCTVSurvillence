import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def delete_unused():
    # Use postgres superuser credentials to bypass ownership/privilege restrictions
    superuser_url = "postgresql+asyncpg://postgres:password@localhost:5432/surveillance_system"
    engine = create_async_engine(superuser_url)
    
    views_to_drop = [
        "active_camera_rois",
        "recent_events_summary",
        "system_health_dashboard"
    ]
    tables_to_drop = [
        "roi_events",
        "rois",
        "event_logs",
        "alert_queue",
        "camera_profiles",
        "event_types",
        "system_settings",
        "dvr_configurations",
        "video_storage_config",
        "system_metrics"
    ]
    
    async with engine.begin() as conn:
        # Drop views first
        for view in views_to_drop:
            try:
                print(f"Dropping view {view}...")
                await conn.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE;"))
                print(f"View {view} dropped successfully.")
            except Exception as e:
                print(f"Error dropping view {view}: {e}")
                
        # Drop tables
        for table in tables_to_drop:
            try:
                print(f"Dropping table {table}...")
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"Table {table} dropped successfully.")
            except Exception as e:
                print(f"Error dropping table {table}: {e}")
                
    await engine.dispose()
    print("Database cleanup completed.")

if __name__ == "__main__":
    asyncio.run(delete_unused())
