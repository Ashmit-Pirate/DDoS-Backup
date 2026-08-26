import pytest
from fastapi.testclient import TestClient
from api.main import app
from db.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

# Setup test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_get_status(client):
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() in ["NORMAL", "ATTACK_DETECTED", "CLASSIFIED", "MITIGATING", "RECOVERING", "RECOVERED"]

def test_get_events(client):
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert "logs" in data
    
    if data["logs"]:
        log = data["logs"][0]
        assert "id" in log
        assert "time" in log
        assert "severity" in log
        assert "component" in log
        assert "message" in log
        assert "incidentId" in log
        
    if data["incidents"]:
        inc = data["incidents"][0]
        assert "id" in inc
        assert "status" in inc
        assert "type" in inc
        assert "severity" in inc
        assert "start" in inc
        assert "detectionTime" in inc
        assert "mitigationTime" in inc
        assert "duration" in inc

def test_get_mitigation_active(client):
    response = client.get("/api/v1/mitigation/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        mit = data[0]
        assert "id" in mit
        assert "name" in mit
        assert "status" in mit
        assert "result" in mit
        assert "sourceIp" in mit

def test_get_config(client):
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "targetApplication" in data
    assert "environment" in data
    assert "mitigationMode" in data
    assert "telemetryRefreshRateMs" in data
    assert "serverAvailability" in data
    assert "baselineRequestRate" in data
    assert "baselineEntropy" in data
