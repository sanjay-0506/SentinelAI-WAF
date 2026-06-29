from typing import Optional

import redis.asyncio as aioredis

_redis_client: Optional[aioredis.Redis] = None


async def init_redis(redis_url: str) -> None:
    global _redis_client
    _redis_client = aioredis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    # Verify connectivity on startup
    await _redis_client.ping()


def get_redis() -> aioredis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis not initialised. Call init_redis() first.")
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
