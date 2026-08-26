import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from db.redis_client import get_redis_client
from db.models import Event

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def publish_event(
    event_type: str,
    data: Dict[str, Any],
    db: Optional[Session] = None,
    db_args: Optional[Dict[str, Any]] = None,
) -> None:
    """
    1. Persist the event to the PostgreSQL `events` table (if db provided).
    2. Publish to Redis `channel:events`.
    """
    if db is not None and db_args is not None:
        try:
            db_event = Event(**db_args)
            db.add(db_event)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Warning: Failed to write event to DB: {e}")

    envelope = {
        "type": event_type,
        "timestamp": utcnow_iso(),
        "data": data
    }
    try:
        client = get_redis_client()
        await client.publish("channel:events", json.dumps(envelope))
    except Exception as e:
        print(f"Warning: Failed to publish event to Redis: {e}")
