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


# ─── Session 2: Decision/Mitigation state helpers ─────────────────


async def increment_rate_counter(source_ip: str, window_seconds: int = 60) -> int:
    """
    Increment the sliding-window rate counter for a source IP.
    Key: rate:{source_ip}
    TTL is set only on the first increment (counter == 1) to avoid
    resetting the window on subsequent requests within the same period.

    Returns the current count within the window.
    """
    client = get_redis_client()
    key = f"rate:{source_ip}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)
    return count


async def increment_detection_counter(
    source_ip: str, attack_type: str, window_seconds: int = 300
) -> int:
    """
    Increment the repeated-detection counter for a source IP + attack type.
    Key: detect:{source_ip}:{attack_type}
    TTL is set only on the first increment to avoid resetting the window.

    Returns the repeated-detection count within the window.
    """
    client = get_redis_client()
    key = f"detect:{source_ip}:{attack_type}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)
    return count


async def set_mitigation_active(
    source_ip: str, cooldown_seconds: int = 300
) -> bool:
    """
    Set the active-mitigation flag for a source IP with a TTL cooldown.
    Key: mitigation:{source_ip}
    Uses SET ... NX EX — only sets if the key does not already exist.
    TTL expiry IS the cooldown auto-unblock mechanism (no cron job).

    Returns True if newly set, False if the key already existed
    (source_ip is still under cooldown from a prior mitigation).
    """
    from datetime import datetime, timezone

    client = get_redis_client()
    key = f"mitigation:{source_ip}"
    timestamp = datetime.now(timezone.utc).isoformat()
    result = await client.set(key, timestamp, ex=cooldown_seconds, nx=True)
    return result is not None and result is not False


async def is_mitigation_active(source_ip: str) -> bool:
    """
    Check whether a source IP currently has an active mitigation.
    Key: mitigation:{source_ip}
    Returns True if the key exists (TTL has not yet expired).
    """
    client = get_redis_client()
    key = f"mitigation:{source_ip}"
    return bool(await client.exists(key))


async def get_rate_counter(source_ip: str) -> int:
    """
    Read the current rate counter for a source IP without incrementing.
    Key: rate:{source_ip}
    Returns 0 if the key does not exist.
    """
    client = get_redis_client()
    key = f"rate:{source_ip}"
    val = await client.get(key)
    return int(val) if val else 0


async def get_detection_counter(source_ip: str, attack_type: str) -> int:
    """
    Read the current repeated-detection counter for a source IP + attack type
    without incrementing it.
    Key: detect:{source_ip}:{attack_type}
    Returns 0 if the key does not exist.
    """
    client = get_redis_client()
    key = f"detect:{source_ip}:{attack_type}"
    val = await client.get(key)
    return int(val) if val else 0
