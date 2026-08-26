import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from db.redis_client import get_redis_client

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    from api.main import get_allowed_origins
    allowed_origins = get_allowed_origins()
    origin = websocket.headers.get("origin")
    if origin and origin not in allowed_origins and "*" not in allowed_origins:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    client = get_redis_client()
    pubsub = client.pubsub()
    await pubsub.subscribe("channel:events")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe("channel:events")
