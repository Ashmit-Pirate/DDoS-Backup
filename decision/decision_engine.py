"""
Decision engine orchestrator.

Sits between ML prediction and mitigation — the mandatory checkpoint
that prevents any direct ML → block path. For Benign predictions,
returns ALLOW immediately without touching any Redis state. For attack
predictions, increments rate/detection counters, computes risk, and
maps severity to an action (ALLOW / MONITOR / MITIGATE).

The gatekeeper's escalation to the investigator (already in prediction.py)
is NOT the block decision — that distinction is already correctly
implemented there. This engine makes the actual block/mitigate decision
using the multiclass model's output + contextual Redis state, never
the gatekeeper's raw verdict alone.
"""

from typing import Dict, Any

from db.redis_client import increment_rate_counter, increment_detection_counter
from decision.risk_score import compute_risk


# Severity → action mapping
_SEVERITY_TO_ACTION: Dict[str, str] = {
    "HIGH": "MITIGATE",
    "MEDIUM": "MONITOR",
    "LOW": "MONITOR",
}


async def evaluate(prediction: Dict[str, Any], source_ip: str) -> Dict[str, Any]:
    """
    Evaluate a prediction and produce a decision.

    For Benign predictions (is_attack=False): returns immediately with
    {risk_score: 0, severity: LOW, action: ALLOW, factors: None}.
    No Redis counters are touched. No risk_assessments row is created.

    For attack predictions (is_attack=True): increments Redis rate and
    detection counters, computes risk score/severity, and maps severity
    to an action.

    Args:
        prediction: Dict from predict_flow() with keys:
                    predicted_class, confidence, gatekeeper_confidence, is_attack.
        source_ip:  Source IP from the flow metadata.

    Returns:
        {
            "risk_score": int (0-100),
            "severity": str ("LOW" | "MEDIUM" | "HIGH"),
            "action": str ("ALLOW" | "MONITOR" | "MITIGATE"),
            "factors": dict | None,
        }
    """
    # ── Benign fast path ──────────────────────────────────────────────
    # Benign flows NEVER touch Redis rate/repeat state and NEVER produce
    # risk_assessments or mitigation_actions rows.
    if not prediction.get("is_attack", False):
        return {
            "risk_score": 0,
            "severity": "LOW",
            "action": "ALLOW",
            "factors": None,
        }

    # ── Attack path ───────────────────────────────────────────────────
    predicted_class = prediction["predicted_class"]

    # 1. Increment rate counter (sliding window)
    await increment_rate_counter(source_ip)

    # 2. Increment repeated-detection counter for this source_ip + attack_type.
    #    This MUST happen BEFORE compute_risk so the risk scorer sees the
    #    post-increment value (see threshold comment in risk_score.py).
    await increment_detection_counter(source_ip, predicted_class)

    # 3. Compute risk score and severity
    risk = await compute_risk(prediction, source_ip)

    # 4. Map severity to action
    severity = risk["severity"]
    action = _SEVERITY_TO_ACTION.get(severity, "MONITOR")

    return {
        "risk_score": risk["risk_score"],
        "severity": severity,
        "action": action,
        "factors": risk["factors"],
    }
