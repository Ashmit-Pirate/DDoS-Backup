import pytest
import asyncio
import json
import httpx
import websockets

@pytest.mark.asyncio
async def test_ws_integration():
    """Test WS connection, trigger detection and verify events against the live backend."""
    
    # This requires the backend to be running on localhost:8000
    try:
        async with websockets.connect("ws://localhost:8000/ws/live") as websocket:
            
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
            
            await asyncio.sleep(0.5)
            
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8000/api/v1/detect", json=payload)
                assert response.status_code == 200
            
            events = []
            try:
                for _ in range(3):
                    msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    events.append(json.loads(msg))
            except Exception:
                pass
            
            assert len(events) >= 1
            
            has_detection = False
            for evt in events:
                if evt["type"] == "detection":
                    has_detection = True
                    data = evt["data"]
                    assert "prediction" in data
                    assert "confidence" in data
                    assert "risk" in data
                    assert data["risk"] is not None
            
            assert has_detection
    except ConnectionRefusedError:
        pytest.skip("Live backend not running on port 8000, skipping WS integration test")
