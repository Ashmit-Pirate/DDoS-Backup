"""
Mitigation engine — simulation mode.

Given a decision (from the decision engine), a prediction, and a source IP:
- If action == MITIGATE and the source_ip is not already under cooldown,
  looks up the attack-specific policy, writes a mitigation_actions row
  with status='SIMULATED', and sets the Redis cooldown TTL.
- If action != MITIGATE, or if the source_ip is already under cooldown,
  returns None — no mitigation_actions row is written.

status is ALWAYS 'SIMULATED' in this session. No enforcement logic
(nftables/iptables/NGINX) exists anywhere — that's explicitly out of
scope for this session and the whole current build plan.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from db.models import MitigationAction
from db.redis_client import is_mitigation_active, set_mitigation_active
from mitigation.mitigation_policy import get_policy, DEFAULT_COOLDOWN_SECONDS


async def execute_mitigation(
    decision: Dict[str, Any],
    prediction: Dict[str, Any],
    source_ip: str,
    risk_assessment_id: UUID,
    db: Session,
) -> Optional[MitigationAction]:
    """
    Execute mitigation for an attack if warranted by the decision.

    Args:
        decision:           Dict from decision_engine.evaluate() with 'action' key.
        prediction:         Dict from predict_flow() with 'predicted_class' key.
        source_ip:          Source IP from flow metadata.
        risk_assessment_id: UUID of the corresponding risk_assessments row (FK).
        db:                 SQLAlchemy session.

    Returns:
        The created MitigationAction ORM object if mitigation was executed,
        or None if no mitigation was needed/allowed.
    """
    # 1. Only act on MITIGATE decisions — MONITOR/ALLOW produce no row.
    if decision.get("action") != "MITIGATE":
        return None

    # 2. Check if source_ip is already under active mitigation (cooldown).
    #    Avoids duplicate mitigation_actions rows per the architecture's
    #    idempotency requirement.
    if await is_mitigation_active(source_ip):
        return None

    # 3. Look up attack-specific policy.
    attack_type = prediction["predicted_class"]
    policy = get_policy(attack_type)
    if policy is None:
        # Defensive — shouldn't happen for valid attack types, but don't
        # crash on an unexpected class from the ML model.
        return None

    # 4. Set the Redis cooldown flag (NX — only if not already set).
    #    If another concurrent request set it between our EXISTS check
    #    and this SET, the NX flag prevents a duplicate.
    newly_set = await set_mitigation_active(source_ip, cooldown_seconds=DEFAULT_COOLDOWN_SECONDS)
    if not newly_set:
        return None

    # 5. Compute expiry timestamp for the DB record.
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=DEFAULT_COOLDOWN_SECONDS)

    # 6. Write the mitigation_actions row — ALWAYS status='SIMULATED'.
    record = MitigationAction(
        risk_assessment_id=risk_assessment_id,
        attack_type=attack_type,
        action_type=policy["action_type"],
        status="SIMULATED",
        source_ip=source_ip,
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()  # Flush to get the generated id, but let the caller commit.

    return record
