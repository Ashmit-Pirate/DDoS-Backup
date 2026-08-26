"""
Unit tests for the decision engine (decision_engine.py + risk_score.py).

Tests use mocked Redis to isolate the decision logic from a running Redis instance.
The critical test here is test_first_high_confidence_attack_no_mitigation — it
explicitly proves the "no direct ML → block" invariant: a single raw high-confidence
attack prediction, with zero repeat history, must NOT trigger MITIGATE.
"""

import pytest
from unittest.mock import AsyncMock, patch


# ── Benign fast-path ──────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("decision.decision_engine.increment_detection_counter", new_callable=AsyncMock)
@patch("decision.decision_engine.increment_rate_counter", new_callable=AsyncMock)
async def test_benign_returns_allow_no_redis(mock_rate, mock_detect):
    """
    Benign prediction → ALLOW immediately, Redis rate/detection
    counters are NEVER called.
    """
    from decision.decision_engine import evaluate

    prediction = {
        "predicted_class": "Benign",
        "confidence": 0.9823,
        "gatekeeper_confidence": 0.0177,
        "is_attack": False,
    }
    result = await evaluate(prediction, "192.168.1.100")

    assert result["severity"] == "LOW"
    assert result["action"] == "ALLOW"
    assert result["risk_score"] == 0
    assert result["factors"] is None

    # Redis counters must NOT have been called
    mock_rate.assert_not_called()
    mock_detect.assert_not_called()


# ── Explicit negative test: first high-confidence attack ─────────────


@pytest.mark.asyncio
@patch("decision.risk_score.is_mitigation_active", new_callable=AsyncMock, return_value=False)
@patch("decision.risk_score.get_detection_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.risk_score.get_rate_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.decision_engine.increment_detection_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.decision_engine.increment_rate_counter", new_callable=AsyncMock, return_value=1)
async def test_first_high_confidence_attack_no_mitigation(
    mock_rate, mock_detect, mock_get_rate, mock_get_detection, mock_is_mitigated
):
    """
    EXPLICIT NEGATIVE TEST — THE LOAD-BEARING INVARIANT:
    A single raw high-confidence attack prediction (confidence=0.99),
    with zero prior rate/repeat context (first time this source_ip has
    ever been seen — repeat_count=1 post-increment), must NOT trigger
    MITIGATE. It should get MEDIUM severity and MONITOR action.

    This is what actually proves the "no direct ML → block" rule.
    """
    from decision.decision_engine import evaluate

    prediction = {
        "predicted_class": "Syn",
        "confidence": 0.99,
        "gatekeeper_confidence": 0.95,
        "is_attack": True,
    }

    result = await evaluate(prediction, "10.0.0.99")

    # Must NOT be MITIGATE — first detection, repeat_count=1 < 3
    assert result["action"] == "MONITOR", (
        f"First high-confidence attack must NOT trigger MITIGATE, got action={result['action']}"
    )
    assert result["severity"] == "MEDIUM", (
        f"confidence=0.99 > 0.80 but repeat_count=1 < 3, expected MEDIUM, got {result['severity']}"
    )
    assert result["action"] != "MITIGATE"


# ── Repeated high-confidence attack → HIGH/MITIGATE ──────────────────


@pytest.mark.asyncio
@patch("decision.risk_score.is_mitigation_active", new_callable=AsyncMock, return_value=False)
@patch("decision.risk_score.get_detection_counter", new_callable=AsyncMock, return_value=3)
@patch("decision.risk_score.get_rate_counter", new_callable=AsyncMock, return_value=5)
@patch("decision.decision_engine.increment_detection_counter", new_callable=AsyncMock, return_value=3)
@patch("decision.decision_engine.increment_rate_counter", new_callable=AsyncMock, return_value=5)
async def test_repeated_high_confidence_triggers_high(
    mock_rate, mock_detect, mock_get_rate, mock_get_detection, mock_is_mitigated
):
    """
    confidence=0.99, repeat_count=3 (3rd detection within window)
    → HIGH severity, MITIGATE action.
    """
    from decision.decision_engine import evaluate

    prediction = {
        "predicted_class": "Syn",
        "confidence": 0.99,
        "gatekeeper_confidence": 0.95,
        "is_attack": True,
    }

    result = await evaluate(prediction, "10.0.0.99")

    assert result["severity"] == "HIGH"
    assert result["action"] == "MITIGATE"
    assert result["risk_score"] >= 70


# ── Low confidence → LOW severity ─────────────────────────────────────


@pytest.mark.asyncio
@patch("decision.risk_score.is_mitigation_active", new_callable=AsyncMock, return_value=False)
@patch("decision.risk_score.get_detection_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.risk_score.get_rate_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.decision_engine.increment_detection_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.decision_engine.increment_rate_counter", new_callable=AsyncMock, return_value=1)
async def test_low_confidence_attack_returns_low(
    mock_rate, mock_detect, mock_get_rate, mock_get_detection, mock_is_mitigated
):
    """
    confidence=0.60 (below 0.80 threshold) → LOW severity, MONITOR action.
    """
    from decision.decision_engine import evaluate

    prediction = {
        "predicted_class": "UDP",
        "confidence": 0.60,
        "gatekeeper_confidence": 0.85,
        "is_attack": True,
    }

    result = await evaluate(prediction, "10.0.0.50")

    assert result["severity"] == "LOW"
    assert result["action"] == "MONITOR"
    assert result["risk_score"] < 40


# ── Medium confidence → MEDIUM severity ───────────────────────────────


@pytest.mark.asyncio
@patch("decision.risk_score.is_mitigation_active", new_callable=AsyncMock, return_value=False)
@patch("decision.risk_score.get_detection_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.risk_score.get_rate_counter", new_callable=AsyncMock, return_value=2)
@patch("decision.decision_engine.increment_detection_counter", new_callable=AsyncMock, return_value=1)
@patch("decision.decision_engine.increment_rate_counter", new_callable=AsyncMock, return_value=2)
async def test_medium_confidence_returns_medium(
    mock_rate, mock_detect, mock_get_rate, mock_get_detection, mock_is_mitigated
):
    """
    confidence=0.85 (above 0.80 but below 0.95), repeat_count=1
    → MEDIUM severity, MONITOR action.
    """
    from decision.decision_engine import evaluate

    prediction = {
        "predicted_class": "LDAP",
        "confidence": 0.85,
        "gatekeeper_confidence": 0.90,
        "is_attack": True,
    }

    result = await evaluate(prediction, "10.0.0.51")

    assert result["severity"] == "MEDIUM"
    assert result["action"] == "MONITOR"
    assert 40 <= result["risk_score"] <= 69
