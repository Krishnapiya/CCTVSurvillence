import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings

logger = logging.getLogger("fall_detection.database")

def get_db_connection():
    """
    Establish a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=3
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        return None

def init_db():
    """
    Initialize the database using schema.sql.
    """
    conn = get_db_connection()
    if not conn:
        logger.warning("Database connection unavailable. Skipping schema initialization.")
        return False
    
    try:
        with conn.cursor() as cur:
            schema_path = settings.BASE_DIR / "schema.sql"
            if schema_path.exists():
                logger.info(f"Loading schema from {schema_path}")
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                cur.execute(schema_sql)
                conn.commit()
                logger.info("Database schema initialized successfully.")
                return True
            else:
                logger.error("schema.sql not found!")
                return False
    except Exception as e:
        logger.error(f"Error during schema initialization: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# In-memory storage fallback for local testing when database is unavailable
MOCK_EVENTS = []
mock_id_counter = 1

def save_event(person_id: int, confidence_score: float, screenshot_path: str, video_path: str, details: dict = None) -> int:
    """
    Insert a new fall/fainting event record into the database.
    Falls back to in-memory list if the database is unavailable.
    """
    global mock_id_counter
    conn = get_db_connection()
    if not conn:
        logger.warning("Database unavailable. Event logged in-memory instead.")
        from datetime import datetime, timezone
        event = {
            "event_id": mock_id_counter,
            "person_id": person_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence_score": confidence_score,
            "screenshot_path": screenshot_path,
            "video_path": video_path,
            "details": details
        }
        MOCK_EVENTS.insert(0, event)
        current_id = mock_id_counter
        mock_id_counter += 1
        return current_id
    
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO events (person_id, confidence_score, screenshot_path, video_path, details)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING event_id;
            """
            details_json = json.dumps(details) if details else None
            cur.execute(query, (person_id, confidence_score, screenshot_path, video_path, details_json))
            event_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully logged event to DB. Event ID: {event_id}")
            return event_id
    except Exception as e:
        logger.error(f"Failed to save event to database: {e}")
        if conn:
            conn.rollback()
        return -1
    finally:
        if conn:
            conn.close()

def get_events(limit: int = 50) -> list:
    """
    Retrieve stored events from the database, falling back to in-memory list.
    """
    conn = get_db_connection()
    if not conn:
        logger.warning("Database unavailable. Returning mock events list.")
        return MOCK_EVENTS[:limit]
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT event_id, person_id, timestamp, confidence_score, screenshot_path, video_path, details
                FROM events
                ORDER BY timestamp DESC
                LIMIT %s;
            """
            cur.execute(query, (limit,))
            events = cur.fetchall()
            
            # Format timestamp to ISO format for easier consumption in API/Frontend
            for event in events:
                if event['timestamp']:
                    event['timestamp'] = event['timestamp'].isoformat()
                if event['details'] and isinstance(event['details'], str):
                    event['details'] = json.loads(event['details'])
            return list(events)
    except Exception as e:
        logger.error(f"Failed to fetch events from database: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_latest_event() -> dict:
    """
    Retrieve the single latest event from the database, falling back to in-memory list.
    """
    conn = get_db_connection()
    if not conn:
        logger.warning("Database unavailable. Returning latest mock event.")
        return MOCK_EVENTS[0] if MOCK_EVENTS else {}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT event_id, person_id, timestamp, confidence_score, screenshot_path, video_path, details
                FROM events
                ORDER BY timestamp DESC
                LIMIT 1;
            """
            cur.execute(query)
            event = cur.fetchone()
            if event:
                if event['timestamp']:
                    event['timestamp'] = event['timestamp'].isoformat()
                if event['details'] and isinstance(event['details'], str):
                    event['details'] = json.loads(event['details'])
                return dict(event)
            return {}
    except Exception as e:
        logger.error(f"Failed to fetch latest event from database: {e}")
        return {}
    finally:
        if conn:
            conn.close()
