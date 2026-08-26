from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from db.database import get_db
from db.models import MitigationAction as MitigationActionModel
from api.schemas import MitigationData
from typing import List

router = APIRouter(prefix="/api/v1", tags=["Mitigation"])

@router.get("/mitigation/active", response_model=List[MitigationData])
async def get_active_mitigations(db: Session = Depends(get_db)):
    # The requirement: GET /api/v1/mitigation/active -> MitigationAction[] including sourceIp
    # Return all SIMULATED or ACTIVE mitigations.
    records = db.query(MitigationActionModel).filter(
        MitigationActionModel.status.in_(["SIMULATED", "ACTIVE", "PLANNED"])
    ).order_by(desc(MitigationActionModel.started_at)).all()
    
    results = []
    action_names = {
        "RATE_LIMIT": "Connection rate limiting",
        "RATE_LIMIT_AND_FILTER": "UDP rate limiting + filtering",
        "RESTRICT_EXPOSURE": "Restrict exposure",
        "FILTER_AND_RATE_LIMIT": "Filtering + rate limiting",
        "RESTRICT_TRAFFIC": "Restrict unnecessary traffic"
    }
    
    for r in records:
        name = action_names.get(r.action_type, "Mitigation applied")
        result_str = f"Would apply {r.action_type} to {r.source_ip}" if r.status == "SIMULATED" else f"Applied {r.action_type} to {r.source_ip}"
        
        results.append(MitigationData(
            id=str(r.id),
            name=name,
            status=r.status,
            result=result_str,
            sourceIp=r.source_ip
        ))
    return results
