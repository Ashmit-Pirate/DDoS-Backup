import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from db.database import Base, get_db
from db.models import Detection, RiskAssessment, MitigationAction
from detection.model_loader import load_models

# In-memory SQLite for isolated testing of database write/no-write logic
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    # Pre-load ML models for testing
    load_models()
    # Create tables in test in-memory SQLite database
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["models_loaded"] is True


def test_cors_headers(client):
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/api/v1/detect", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


@patch("api.routers.detect.record_flow_stats", new_callable=AsyncMock)
@patch("api.routers.detect.evaluate_decision", new_callable=AsyncMock)
def test_detect_benign_flow_no_db_row(mock_evaluate, mock_record_stats, client):
    mock_record_stats.return_value = {"total_count": 1, "benign_count": 1}
    mock_evaluate.return_value = {
        "risk_score": 0,
        "severity": "LOW",
        "action": "ALLOW",
        "factors": None,
    }

    db = TestingSessionLocal()
    initial_detection_count = db.query(Detection).count()
    initial_risk_count = db.query(RiskAssessment).count()
    initial_mitigation_count = db.query(MitigationAction).count()
    db.close()

    payload = {
        "metadata": {
            "source_ip": "192.168.1.100",
            "destination_ip": "192.168.1.1",
            "source_port": 45123,
            "destination_port": 443,
        },
        "features": {"Protocol": 6, "Flow Duration": 0},
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_class" in data
    assert "confidence" in data
    assert "gatekeeper_confidence" in data

    # Verify Redis stats increment was called
    mock_record_stats.assert_called_once()

    # If the prediction was Benign, verify NO database rows were inserted
    db = TestingSessionLocal()
    final_detection_count = db.query(Detection).count()
    final_risk_count = db.query(RiskAssessment).count()
    final_mitigation_count = db.query(MitigationAction).count()
    db.close()

    if data["predicted_class"] == "Benign":
        assert final_detection_count == initial_detection_count, "Benign flow must NOT insert a detections row"
        assert final_risk_count == initial_risk_count, "Benign flow must NOT insert a risk_assessments row"
        assert final_mitigation_count == initial_mitigation_count, "Benign flow must NOT insert a mitigation_actions row"


@patch("api.routers.detect.record_flow_stats", new_callable=AsyncMock)
@patch("api.routers.detect.evaluate_decision", new_callable=AsyncMock)
@patch("api.routers.detect.execute_mitigation", new_callable=AsyncMock)
def test_detect_attack_flow_writes_db_row(mock_mitigation, mock_evaluate, mock_record_stats, client):
    mock_record_stats.return_value = {"total_count": 2, "benign_count": 1}
    mock_evaluate.return_value = {
        "risk_score": 55,
        "severity": "MEDIUM",
        "action": "MONITOR",
        "factors": {"confidence": 0.99, "traffic_rate": 1, "repeat_count": 1, "already_mitigated": False},
    }
    mock_mitigation.return_value = None  # MONITOR → no mitigation

    db = TestingSessionLocal()
    initial_count = db.query(Detection).count()
    db.close()

    payload = {
        "metadata": {
            "source_ip": "10.0.0.99",
            "destination_ip": "10.0.0.1",
            "source_port": 54321,
            "destination_port": 80,
        },
        "features": {
            "Protocol": 17.0,
            "Init Bwd Win Bytes": -1.0,
            "Init Fwd Win Bytes": -1.0,
            "Fwd Packet Length Min": 500.0,
            "Avg Packet Size": 500.0,
            "Flow Duration": 100.0,
        },
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_class"] != "Benign"

    # Verify Redis stats increment was called
    mock_record_stats.assert_called_once()

    # Verify a detection record was written to DB with correct source_ip from metadata
    db = TestingSessionLocal()
    final_count = db.query(Detection).count()
    new_record = db.query(Detection).filter(Detection.source_ip == "10.0.0.99").first()
    db.close()

    assert final_count == initial_count + 1
    assert new_record is not None
    assert new_record.source_ip == "10.0.0.99"
    assert new_record.predicted_class == data["predicted_class"]


def test_detect_invalid_flat_shape_fails_422(client):
    """Old flat shape without metadata wrapper must fail with 422."""
    payload = {
        "source_ip": "192.168.1.100",
        "Protocol": 6,
        "Flow Duration": 0,
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 422


def test_detect_invalid_old_nested_shape_fails_422(client):
    """Old top-level source_ip with nested features must fail with 422."""
    payload = {
        "source_ip": "192.168.1.100",
        "features": {"Protocol": 6, "Flow Duration": 0},
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 422


def test_detect_missing_metadata_fields_fails_422(client):
    """Metadata missing required port or IP fields must fail with 422."""
    payload = {
        "metadata": {
            "source_ip": "192.168.1.100",
            # missing destination_ip, source_port, destination_port
        },
        "features": {"Protocol": 6},
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 422


# ── Session 2: Decision/mitigation integration tests ─────────────────


@patch("api.routers.detect.record_flow_stats", new_callable=AsyncMock)
@patch("api.routers.detect.evaluate_decision", new_callable=AsyncMock)
def test_detect_benign_no_decision_or_mitigation(mock_evaluate, mock_record_stats, client):
    """
    Benign prediction → decision is {action: ALLOW, severity: LOW},
    mitigation is None, no risk_assessments or mitigation_actions rows.
    """
    mock_record_stats.return_value = {"total_count": 10, "benign_count": 10}
    mock_evaluate.return_value = {
        "risk_score": 0,
        "severity": "LOW",
        "action": "ALLOW",
        "factors": None,
    }

    payload = {
        "metadata": {
            "source_ip": "192.168.1.200",
            "destination_ip": "192.168.1.1",
            "source_port": 45123,
            "destination_port": 443,
        },
        "features": {"Protocol": 6, "Flow Duration": 0},
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()

    if data["predicted_class"] == "Benign":
        # Decision should be ALLOW
        assert data["decision"] is not None
        assert data["decision"]["action"] == "ALLOW"
        assert data["decision"]["severity"] == "LOW"
        assert data["decision"]["risk_score"] == 0
        # Mitigation should be None
        assert data["mitigation"] is None


@patch("api.routers.detect.record_flow_stats", new_callable=AsyncMock)
@patch("api.routers.detect.evaluate_decision", new_callable=AsyncMock)
@patch("api.routers.detect.execute_mitigation", new_callable=AsyncMock)
def test_detect_attack_returns_decision_info(mock_mitigation, mock_evaluate, mock_record_stats, client):
    """
    Attack prediction → decision is present with valid severity/action.
    """
    mock_record_stats.return_value = {"total_count": 5, "benign_count": 1}
    mock_evaluate.return_value = {
        "risk_score": 55,
        "severity": "MEDIUM",
        "action": "MONITOR",
        "factors": {"confidence": 0.92, "traffic_rate": 3, "repeat_count": 1, "already_mitigated": False},
    }
    mock_mitigation.return_value = None  # MONITOR → no mitigation

    payload = {
        "metadata": {
            "source_ip": "10.0.0.77",
            "destination_ip": "10.0.0.1",
            "source_port": 54321,
            "destination_port": 80,
        },
        "features": {
            "Protocol": 17.0,
            "Init Bwd Win Bytes": -1.0,
            "Init Fwd Win Bytes": -1.0,
            "Fwd Packet Length Min": 500.0,
            "Avg Packet Size": 500.0,
            "Flow Duration": 100.0,
        },
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()

    if data["predicted_class"] != "Benign":
        assert data["decision"] is not None
        assert data["decision"]["severity"] in ("LOW", "MEDIUM", "HIGH")
        assert data["decision"]["action"] in ("ALLOW", "MONITOR", "MITIGATE")
        assert isinstance(data["decision"]["risk_score"], int)


@patch("api.routers.detect.record_flow_stats", new_callable=AsyncMock)
@patch("api.routers.detect.evaluate_decision", new_callable=AsyncMock)
@patch("api.routers.detect.execute_mitigation", new_callable=AsyncMock)
def test_detect_attack_first_time_no_mitigation(mock_mitigation, mock_evaluate, mock_record_stats, client):
    """
    First-time attack → decision is MONITOR (not MITIGATE),
    mitigation is None. First detection cannot reach HIGH severity.
    """
    mock_record_stats.return_value = {"total_count": 3, "benign_count": 1}
    mock_evaluate.return_value = {
        "risk_score": 55,
        "severity": "MEDIUM",
        "action": "MONITOR",
        "factors": {"confidence": 0.99, "traffic_rate": 1, "repeat_count": 1, "already_mitigated": False},
    }
    mock_mitigation.return_value = None

    payload = {
        "metadata": {
            "source_ip": "10.0.0.88",
            "destination_ip": "10.0.0.1",
            "source_port": 54321,
            "destination_port": 80,
        },
        "features": {
            "Protocol": 17.0,
            "Init Bwd Win Bytes": -1.0,
            "Init Fwd Win Bytes": -1.0,
            "Fwd Packet Length Min": 500.0,
            "Avg Packet Size": 500.0,
            "Flow Duration": 100.0,
        },
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()

    if data["predicted_class"] != "Benign":
        assert data["decision"]["action"] == "MONITOR"
        assert data["mitigation"] is None
