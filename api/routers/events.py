from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from db.database import get_db
from db.models import Event, MitigationAction
from api.schemas import EventsResponse, Incident, LogEvent
from typing import List
import uuid

router = APIRouter(prefix="/api/v1", tags=["Events"])

@router.get("/events", response_model=EventsResponse)
async def get_events(limit: int = Query(50, ge=1), db: Session = Depends(get_db)):
    events = db.query(Event).order_by(desc(Event.timestamp)).limit(limit).all()
    
    logs: List[LogEvent] = []
    for e in events:
        severity_map = {
            "LOW": "INFO",
            "MEDIUM": "WARN",
            "HIGH": "ALERT"
        }
        if not e.action:
            msg = f"Detected {e.attack_type} attack (confidence: {e.confidence:.1%})"
        else:
            if e.action == "MONITOR" and not e.status:
                msg = "MONITOR — traffic flagged, no mitigation triggered"
            else:
                msg = f"{e.action} applied ({e.status})"

        logs.append(LogEvent(
            id=str(e.id),
            time=e.timestamp.isoformat(),
            severity=severity_map.get(e.severity, "INFO"),
            component="DecisionEngine" if not e.action else "Mitigation",
            message=msg,
            incidentId=None
        ))
    
    # We will derive incidents from recent mitigation actions for now
    mitigations = db.query(MitigationAction).order_by(desc(MitigationAction.started_at)).limit(limit).all()
    incidents: List[Incident] = []
    for m in mitigations:
        incidents.append(Incident(
            id=str(m.id),
            status="ACTIVE" if m.status in ("PLANNED", "SIMULATED", "ACTIVE") else "RESOLVED",
            type=m.attack_type,
            severity="HIGH", # we assume mitigations are HIGH severity incidents
            start=m.started_at.isoformat(),
            detectionTime=m.started_at.isoformat(),
            mitigationTime=m.started_at.isoformat(),
            duration="ongoing" if m.status in ("PLANNED", "SIMULATED", "ACTIVE") else "ended"
        ))

    return EventsResponse(incidents=incidents, logs=logs)
