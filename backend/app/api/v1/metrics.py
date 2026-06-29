import time

from fastapi import APIRouter, Request

from app.core.logging_config import get_logger
from app.rules.engine import RuleEngine
from app.schemas.metrics import MetricsResponse
from app.services.cache_service import CacheService
from app.services.metrics_service import MetricsService

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "",
    response_model=MetricsResponse,
    summary="Runtime performance metrics",
    description=(
        "Returns real-time WAF metrics from Redis counters including "
        "request totals, block rates, attack breakdown, and latency percentiles."
    ),
)
async def get_metrics(request: Request) -> MetricsResponse:
    rule_engine: RuleEngine = request.app.state.rule_engine
    start_time: float = request.app.state.start_time

    cache = CacheService()
    metrics_svc = MetricsService(cache=cache)
    raw_metrics = await metrics_svc.get_metrics()

    uptime = time.monotonic() - start_time

    return MetricsResponse(
        requests_total=raw_metrics["requests_total"],
        blocked_total=raw_metrics["blocked_total"],
        allowed_total=raw_metrics["allowed_total"],
        block_rate=raw_metrics["block_rate"],
        sqli_total=raw_metrics["sqli_total"],
        xss_total=raw_metrics["xss_total"],
        path_traversal_total=raw_metrics["path_traversal_total"],
        command_injection_total=raw_metrics["command_injection_total"],
        latency_p50_ms=raw_metrics["latency_p50_ms"],
        latency_p95_ms=raw_metrics["latency_p95_ms"],
        latency_p99_ms=raw_metrics["latency_p99_ms"],
        uptime_seconds=round(uptime, 2),
        rules_loaded=rule_engine.rules_loaded,
    )
