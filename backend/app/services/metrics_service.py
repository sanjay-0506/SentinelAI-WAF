from app.repositories.processed_log_repo import ProcessedLogRepository
from app.services.cache_service import CacheService


class MetricsService:
    """Aggregates runtime metrics from Redis counters and latency samples.

    Optionally falls back to the database for counters that are not yet in
    Redis (e.g. after a Redis restart), but in practice Redis is the primary
    source of truth for real-time metrics.
    """

    def __init__(
        self,
        cache: CacheService,
        db_repo: ProcessedLogRepository | None = None,
    ) -> None:
        self._cache = cache
        self._db_repo = db_repo

    async def get_metrics(self) -> dict:
        """Return an aggregated metrics dict ready for the /metrics endpoint.

        Returns:
            dict with counters, block_rate, attack breakdown, and latency
            percentiles.
        """
        requests_total = await self._cache.get_counter("requests_total")
        blocked_total = await self._cache.get_counter("blocked_total")
        allowed_total = await self._cache.get_counter("allowed_total")
        sqli_total = await self._cache.get_counter("attack_sqli")
        xss_total = await self._cache.get_counter("attack_xss")
        path_total = await self._cache.get_counter("attack_path_traversal")
        cmd_total = await self._cache.get_counter("attack_command_injection")
        latencies = await self._cache.get_latency_percentiles()

        block_rate = (
            blocked_total / requests_total if requests_total > 0 else 0.0
        )

        return {
            "requests_total": requests_total,
            "blocked_total": blocked_total,
            "allowed_total": allowed_total,
            "block_rate": round(block_rate, 4),
            "sqli_total": sqli_total,
            "xss_total": xss_total,
            "path_traversal_total": path_total,
            "command_injection_total": cmd_total,
            "latency_p50_ms": latencies["p50"],
            "latency_p95_ms": latencies["p95"],
            "latency_p99_ms": latencies["p99"],
        }
