import json
import time

from app.core.redis_client import get_redis

_LATENCY_KEY = "waf:metrics:latencies"
_MAX_LATENCY_SAMPLES = 1000


class CacheService:
    """Redis-backed cache and metrics counter service."""

    # ------------------------------------------------------------------ #
    # Stats cache                                                          #
    # ------------------------------------------------------------------ #

    async def get_stats(self) -> dict | None:
        """Return cached stats dict, or None on cache miss."""
        r = get_redis()
        data = await r.get("waf:stats")
        return json.loads(data) if data else None

    async def set_stats(self, stats: dict, ttl: int = 5) -> None:
        """Store stats dict in Redis with the given TTL in seconds."""
        r = get_redis()
        await r.setex("waf:stats", ttl, json.dumps(stats))

    # ------------------------------------------------------------------ #
    # Atomic counters                                                      #
    # ------------------------------------------------------------------ #

    async def incr_counter(self, key: str) -> int:
        """Atomically increment a named counter and return the new value."""
        r = get_redis()
        return await r.incr(f"waf:metrics:{key}")

    async def get_counter(self, key: str) -> int:
        """Return the current value of a named counter (0 if not set)."""
        r = get_redis()
        val = await r.get(f"waf:metrics:{key}")
        return int(val) if val else 0

    # ------------------------------------------------------------------ #
    # Latency tracking                                                     #
    # ------------------------------------------------------------------ #

    async def record_latency(self, latency_ms: float) -> None:
        """Record a latency sample in a capped sorted-set (newest score wins).

        Keeps at most ``_MAX_LATENCY_SAMPLES`` samples using ZREMRANGEBYRANK.
        """
        r = get_redis()
        score = time.time()
        await r.zadd(_LATENCY_KEY, {str(latency_ms): score})
        # Keep only the most recent _MAX_LATENCY_SAMPLES entries
        await r.zremrangebyrank(
            _LATENCY_KEY, 0, -(1 + _MAX_LATENCY_SAMPLES + 1)
        )

    async def get_latency_percentiles(self) -> dict[str, float]:
        """Return p50, p95, and p99 latency percentiles from recorded samples.

        Returns zeros if no samples are available.
        """
        r = get_redis()
        raw_values = await r.zrange(_LATENCY_KEY, 0, -1)
        if not raw_values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        latencies = sorted(float(v) for v in raw_values)
        n = len(latencies)

        def _percentile(pct: float) -> float:
            idx = min(int(n * pct), n - 1)
            return latencies[idx]

        return {
            "p50": _percentile(0.50),
            "p95": _percentile(0.95),
            "p99": _percentile(0.99),
        }
