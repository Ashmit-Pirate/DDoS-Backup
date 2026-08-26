from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import SystemStatus
from typing import Dict

router = APIRouter(prefix="/api/v1", tags=["Status"])

@router.get("/status")
async def get_status(db: Session = Depends(get_db)) -> str:
    record = db.query(SystemStatus).filter(SystemStatus.id == 1).first()
    if record:
        return record.status
    return "NORMAL"
