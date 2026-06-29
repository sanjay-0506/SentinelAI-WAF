import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.rules.engine import RuleEngine
from app.schemas.health import HealthResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Checks PostgreSQL connectivity (SELECT 1), Redis ping, "
        "and reports loaded rule engine state."
    ),
)
async def health_check(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HealthResponse:
    rule_engine: RuleEngine = request.app.state.rule_engine
    settings = request.app.state.settings
    start_time: float = request.app.state.start_time

    # ── PostgreSQL check ──────────────────────────────────────────────────
    postgres_status = "down"
    try:
        await db.execute(text("SELECT 1"))
        postgres_status = "up"
    except Exception as exc:  # noqa: BLE001
        logger.error("health.postgres_down", error=str(exc))

    # ── Redis check ───────────────────────────────────────────────────────
    redis_status = "down"
    try:
        from app.core.redis_client import get_redis

        await get_redis().ping()
        redis_status = "up"
    except Exception as exc:  # noqa: BLE001
        logger.error("health.redis_down", error=str(exc))

    # ── Determine overall status ──────────────────────────────────────────
    if postgres_status == "up" and redis_status == "up":
        overall = "healthy"
    elif postgres_status == "up" or redis_status == "up":
        overall = "degraded"
    else:
        overall = "unhealthy"

    uptime = time.monotonic() - start_time

    return HealthResponse(
        status=overall,
        postgres=postgres_status,
        redis=redis_status,
        rules_loaded=rule_engine.rules_loaded,
        ruleset_version=rule_engine.ruleset_version,
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
    )
