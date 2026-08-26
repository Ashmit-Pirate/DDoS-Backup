import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from db.database import Base, get_db
from db.models import Detection
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
    return TestClient(app)


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
def test_detect_benign_flow_no_db_row(mock_record_stats, client):
    mock_record_stats.return_value = {"total_count": 1, "benign_count": 1}

    db = TestingSessionLocal()
    initial_count = db.query(Detection).count()
    db.close()

    payload = {
        "source_ip": "192.168.1.100",
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

    # If the prediction was Benign, verify NO detections table row was inserted
    db = TestingSessionLocal()
    final_count = db.query(Detection).count()
    db.close()

    if data["predicted_class"] == "Benign":
        assert final_count == initial_count, "Benign flow must NOT insert a row into detections table"


@patch("api.routers.detect.record_flow_stats", new_callable=AsyncMock)
def test_detect_attack_flow_writes_db_row(mock_record_stats, client):
    mock_record_stats.return_value = {"total_count": 2, "benign_count": 1}

    db = TestingSessionLocal()
    initial_count = db.query(Detection).count()
    db.close()

    # Highly distinctive attack vector (elevated gatekeeper & multiclass attack prediction)
    payload = {
        "source_ip": "10.0.0.99",
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

    # Verify a detection record was written to DB
    db = TestingSessionLocal()
    final_count = db.query(Detection).count()
    new_record = db.query(Detection).filter(Detection.source_ip == "10.0.0.99").first()
    db.close()

    assert final_count == initial_count + 1
    assert new_record is not None
    assert new_record.source_ip == "10.0.0.99"
    assert new_record.predicted_class == data["predicted_class"]
