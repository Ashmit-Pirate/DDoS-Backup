"""
Risk scoring module for the DDoS decision engine.

Given a prediction dict (from the two-stage ML cascade) and a source IP,
pulls Redis state (rate counter, repeated-detection count, active mitigation)
and computes a numeric risk score (0-100) bucketed into LOW/MEDIUM/HIGH severity.

This module is ONLY called for attack predictions (is_attack=True).
Benign flows are short-circuited in decision_engine.py before reaching here.
"""

from typing import Dict, Any

from db.redis_client import (
    get_rate_counter,
    get_detection_counter,
    is_mitigation_active,
)


async def compute_risk(prediction: Dict[str, Any], source_ip: str) -> Dict[str, Any]:
    """
    Compute risk score and severity for an attack prediction.

    Args:
        prediction: Dict from predict_flow() — must contain 'confidence',
                    'predicted_class', and 'is_attack' (True).
        source_ip:  The source IP address from the flow metadata.

    Returns:
        {
            "risk_score": int (0-100),
            "severity": str ("LOW" | "MEDIUM" | "HIGH"),
            "factors": {
                "confidence": float,
                "traffic_rate": int,
                "repeat_count": int,
                "already_mitigated": bool,
            },
        }
    """
    confidence: float = prediction["confidence"]
    attack_type: str = prediction["predicted_class"]

    # Pull current state from Redis
    traffic_rate = await get_rate_counter(source_ip)

    # Read the detection counter — the counter was already incremented by
    # decision_engine.py before calling this function, so the value here
    # reflects the POST-increment count.
    repeat_count = await get_detection_counter(source_ip, attack_type)

    already_mitigated = await is_mitigation_active(source_ip)

    # ─── PLACEHOLDER THRESHOLDS — NOT TUNED ───────────────────────────
    # These are starting-point heuristics for development and demo.
    # They have NOT been validated against real CICDDoS2019-style test
    # traffic. Final values should live in the `config` table, not here.
    # Do not mistake these for validated production numbers.
    #
    # NOTE: repeat_count is POST-increment — "repeat_count >= 3" means
    # this is the 3rd total occurrence of this source_ip+attack_type
    # within the window, INCLUDING the current detection, not 3 prior
    # detections plus this one as a 4th confirmation.
    #
    # NOTE: traffic_rate and already_mitigated are recorded for
    # dashboard explainability but do not currently affect severity —
    # only confidence and repeat_count do. Revisit when tuning real
    # thresholds against test traffic.
    # ──────────────────────────────────────────────────────────────────

    if confidence > 0.95 and repeat_count >= 3:
        severity = "HIGH"
        risk_score = min(95, 70 + int(repeat_count * 5) + int(confidence * 10))
    elif confidence > 0.80:
        severity = "MEDIUM"
        risk_score = min(69, 40 + int(confidence * 20) + int(repeat_count * 3))
    else:
        severity = "LOW"
        risk_score = min(39, int(confidence * 30) + int(repeat_count * 2))

    return {
        "risk_score": risk_score,
        "severity": severity,
        "factors": {
            "confidence": confidence,
            "traffic_rate": traffic_rate,
            "repeat_count": repeat_count,
            "already_mitigated": already_mitigated,
        },
    }
