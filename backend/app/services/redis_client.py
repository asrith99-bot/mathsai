"""
Redis client helpers for caching live market data.
Key convention:
  tick:{symbol}         → LiveTick JSON
  signal:{symbol}       → latest active signal JSON
  scanner:all           → full scanner snapshot list
  market:status         → market open/closed status
"""
import json
from typing import Any, Optional
import redis.asyncio as aioredis
from loguru import logger
from app.config import settings

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    """Serialise value as JSON and store with TTL (seconds)."""
    try:
        r = await get_redis()
        await r.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:
        logger.warning(f"Redis SET failed for {key}: {exc}")


async def cache_get(key: str) -> Optional[Any]:
    """Retrieve and deserialise a JSON value from Redis."""
    try:
        r = await get_redis()
        raw = await r.get(key)
        if raw:
            return json.loads(raw)
    except Exception as exc:
        logger.warning(f"Redis GET failed for {key}: {exc}")
    return None


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as exc:
        logger.warning(f"Redis DELETE failed for {key}: {exc}")


async def publish_event(channel: str, payload: Any) -> None:
    """Publish a JSON payload on a Redis pub/sub channel."""
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(payload, default=str))
    except Exception as exc:
        logger.warning(f"Redis PUBLISH failed on {channel}: {exc}")


# ── Convenience wrappers ───────────────────────────────────────

async def set_tick(symbol: str, tick_dict: dict) -> None:
    await cache_set(f"tick:{symbol}", tick_dict, ttl=120)


async def get_tick(symbol: str) -> Optional[dict]:
    return await cache_get(f"tick:{symbol}")


async def set_active_signal(symbol: str, signal_dict: dict) -> None:
    await cache_set(f"signal:{symbol}", signal_dict, ttl=600)


async def get_active_signal(symbol: str) -> Optional[dict]:
    return await cache_get(f"signal:{symbol}")


async def set_market_status(status: str) -> None:
    await cache_set("market:status", status, ttl=60)


async def get_market_status() -> str:
    result = await cache_get("market:status")
    return result if result else "UNKNOWN"
