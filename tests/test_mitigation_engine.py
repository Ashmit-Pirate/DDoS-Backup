"""
Unit tests for the mitigation engine (mitigation_engine.py + mitigation_policy.py).

Tests verify:
- MITIGATE + valid attack → SIMULATED row + correct policy action_type
- MONITOR/ALLOW → no row written
- Cooldown prevents duplicate mitigation rows
- Redis TTL expiry lifts the cooldown
- All 7 attack types have valid policy entries
"""

import asyncio
import uuid

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.database import Base
from db.models import Detection, RiskAssessment, MitigationAction
from mitigation.mitigation_policy import get_policy, MITIGATION_POLICIES


# ── SQLite test database for isolation ────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_tables():
    """Create and tear down tables for each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)





@pytest.fixture
def db_session():
    """Yield a fresh DB session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_prerequisite_rows(db):
    """Create Detection + RiskAssessment rows needed as FK parents."""
    detection = Detection(
        source_ip="10.0.0.99",
        gatekeeper_confidence=0.95,
        predicted_class="Syn",
        confidence=0.99,
    )
    db.add(detection)
    db.flush()

    risk_assessment = RiskAssessment(
        detection_id=detection.id,
        risk_score=85,
        severity="HIGH",
        factors={"confidence": 0.99, "repeat_count": 3},
    )
    db.add(risk_assessment)
    db.flush()

    return detection, risk_assessment


# ── Test: MITIGATE + Syn → SIMULATED row ─────────────────────────────


@pytest.mark.asyncio
@patch("mitigation.mitigation_engine.set_mitigation_active", new_callable=AsyncMock, return_value=True)
@patch("mitigation.mitigation_engine.is_mitigation_active", new_callable=AsyncMock, return_value=False)
async def test_mitigate_syn_writes_simulated_row(mock_is_active, mock_set_active, db_session):
    """
    HIGH/MITIGATE decision + Syn attack → mitigation_actions row with
    status=SIMULATED and action_type=RATE_LIMIT.
    """
    from mitigation.mitigation_engine import execute_mitigation

    _, risk_assessment = _create_prerequisite_rows(db_session)

    decision = {"action": "MITIGATE", "severity": "HIGH", "risk_score": 85}
    prediction = {"predicted_class": "Syn", "confidence": 0.99, "is_attack": True}

    result = await execute_mitigation(
        decision=decision,
        prediction=prediction,
        source_ip="10.0.0.99",
        risk_assessment_id=risk_assessment.id,
        db=db_session,
    )

    assert result is not None
    assert result.status == "SIMULATED"
    assert result.attack_type == "Syn"
    assert result.action_type == "RATE_LIMIT"
    assert result.source_ip == "10.0.0.99"
    assert result.expires_at is not None

    db_session.commit()

    # Verify the row persisted
    count = db_session.query(MitigationAction).count()
    assert count == 1

    mock_set_active.assert_called_once()


# ── Test: MONITOR → no row written ───────────────────────────────────


@pytest.mark.asyncio
async def test_monitor_action_no_mitigation_row(db_session):
    """
    MEDIUM/MONITOR decision → returns None, no mitigation_actions row.
    """
    from mitigation.mitigation_engine import execute_mitigation

    _, risk_assessment = _create_prerequisite_rows(db_session)

    decision = {"action": "MONITOR", "severity": "MEDIUM", "risk_score": 55}
    prediction = {"predicted_class": "Syn", "confidence": 0.85, "is_attack": True}

    result = await execute_mitigation(
        decision=decision,
        prediction=prediction,
        source_ip="10.0.0.99",
        risk_assessment_id=risk_assessment.id,
        db=db_session,
    )

    assert result is None

    count = db_session.query(MitigationAction).count()
    assert count == 0


# ── Test: Cooldown prevents duplicate ─────────────────────────────────


@pytest.mark.asyncio
@patch("mitigation.mitigation_engine.is_mitigation_active", new_callable=AsyncMock, return_value=True)
async def test_cooldown_prevents_duplicate_mitigation(mock_is_active, db_session):
    """
    MITIGATE decision but source_ip is already under cooldown
    → returns None, no duplicate row.
    """
    from mitigation.mitigation_engine import execute_mitigation

    _, risk_assessment = _create_prerequisite_rows(db_session)

    decision = {"action": "MITIGATE", "severity": "HIGH", "risk_score": 85}
    prediction = {"predicted_class": "Syn", "confidence": 0.99, "is_attack": True}

    result = await execute_mitigation(
        decision=decision,
        prediction=prediction,
        source_ip="10.0.0.99",
        risk_assessment_id=risk_assessment.id,
        db=db_session,
    )

    assert result is None

    count = db_session.query(MitigationAction).count()
    assert count == 0


# ── Test: Redis TTL expiry lifts cooldown ────────────────────────────


@pytest.mark.asyncio
async def test_cooldown_ttl_expires():
    """
    Set mitigation with TTL=1s, wait 2s, verify is_mitigation_active returns False.
    Requires a running Redis instance.
    """
    from db.redis_client import set_mitigation_active, is_mitigation_active, get_redis_client

    client = get_redis_client()
    test_ip = f"test-ttl-{uuid.uuid4().hex[:8]}"

    try:
        await client.ping()
    except Exception:
        pytest.skip("Redis not available — skipping TTL expiry test")

    # Clean up any leftover key
    await client.delete(f"mitigation:{test_ip}")

    # Set with a 1-second TTL
    result = await set_mitigation_active(test_ip, cooldown_seconds=1)
    assert result is True

    # Should be active immediately
    assert await is_mitigation_active(test_ip) is True

    # Wait for TTL to expire
    await asyncio.sleep(2)

    # Should no longer be active
    assert await is_mitigation_active(test_ip) is False


# ── Test: All 7 attack types have valid policies ─────────────────────


@pytest.mark.asyncio
async def test_policy_lookup_all_attack_types():
    """
    All 7 attack types in the policy table return valid policy dicts
    with action_type and description keys.
    """
    expected_types = ["Syn", "UDP", "MSSQL", "LDAP", "NetBIOS", "Portmap", "UDPLag"]

    for attack_type in expected_types:
        policy = get_policy(attack_type)
        assert policy is not None, f"No policy found for attack type: {attack_type}"
        assert "action_type" in policy, f"Missing action_type for: {attack_type}"
        assert "description" in policy, f"Missing description for: {attack_type}"

    # Benign should return None
    assert get_policy("Benign") is None

    # Unknown type should return None
    assert get_policy("UnknownAttack") is None

    # Verify we have exactly 7 entries
    assert len(MITIGATION_POLICIES) == 7
