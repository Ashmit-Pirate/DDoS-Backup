"""
Attack-specific mitigation policy table.

Maps each known attack type to its mitigation action and description.
Source of truth: ddos-build-plan.md § "Mitigation policy — attack-specific, staged".

This is a pure data module — no enforcement logic. The mitigation engine
reads these policies and writes SIMULATED-status rows; real enforcement
(nftables/NGINX/WAF) is explicitly out of scope for this session and
for the whole current build plan.
"""

from typing import Dict, Optional


# Each policy specifies the action_type written to mitigation_actions.action_type
# and a human-readable description for the dashboard's explainability panel (Session 3).
#
# action_type values are free-form TEXT (no DB CHECK constraint):
#   RATE_LIMIT, RATE_LIMIT_AND_FILTER, RESTRICT_EXPOSURE,
#   FILTER_AND_RATE_LIMIT, RESTRICT_TRAFFIC
# Do not introduce variants beyond these five without explicit approval.

MITIGATION_POLICIES: Dict[str, Dict[str, str]] = {
    "Syn": {
        "action_type": "RATE_LIMIT",
        "description": "Connection rate limiting",
    },
    "UDP": {
        "action_type": "RATE_LIMIT_AND_FILTER",
        "description": "UDP rate limiting + filtering",
    },
    "MSSQL": {
        "action_type": "RESTRICT_EXPOSURE",
        "description": "Restrict exposure + rate controls",
    },
    "LDAP": {
        "action_type": "FILTER_AND_RATE_LIMIT",
        "description": "LDAP-specific filtering + rate limiting",
    },
    "NetBIOS": {
        "action_type": "RESTRICT_TRAFFIC",
        "description": "Restrict unnecessary NetBIOS traffic",
    },
    "Portmap": {
        "action_type": "RESTRICT_EXPOSURE",
        "description": "Restrict portmapper/RPC exposure",
    },
    "UDPLag": {
        "action_type": "RATE_LIMIT_AND_FILTER",
        "description": "Rate limiting + suspicious-flow filtering",
    },
}

# Redis TTL for the mitigation:{source_ip} key.
# TTL expiry IS the cooldown-based auto-unblock mechanism — no cron job needed.
DEFAULT_COOLDOWN_SECONDS: int = 300  # 5 minutes


def get_policy(attack_type: str) -> Optional[Dict[str, str]]:
    """
    Look up the mitigation policy for a given attack type.

    Returns the policy dict (with 'action_type' and 'description'),
    or None if attack_type is unknown or Benign.
    """
    return MITIGATION_POLICIES.get(attack_type)
