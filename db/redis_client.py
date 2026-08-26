import os
from typing import Optional, Dict
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    """Get or create singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client


async def ping_redis() -> bool:
    """Check Redis connectivity."""
    client = get_redis_client()
    try:
        res = await client.ping()
        return bool(res)
    except Exception:
        return False


async def close_redis() -> None:
    """Close Redis client connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def record_flow_stats(is_benign: bool) -> Dict[str, int]:
    """
    Increment flow traffic counters in Redis.
    stats:total_count is incremented on every flow.
    stats:benign_count is incremented only if the flow is Benign.
    """
    client = get_redis_client()
    total = await client.incr("stats:total_count")
    benign = 0
    if is_benign:
        benign = await client.incr("stats:benign_count")
    else:
        current_benign = await client.get("stats:benign_count")
        benign = int(current_benign) if current_benign else 0
    return {"total_count": total, "benign_count": benign}


async def get_traffic_stats() -> Dict[str, int]:
    """Retrieve current total and benign flow counters."""
    client = get_redis_client()
    total = await client.get("stats:total_count")
    benign = await client.get("stats:benign_count")
    return {
        "total_count": int(total) if total else 0,
        "benign_count": int(benign) if benign else 0,
    }
