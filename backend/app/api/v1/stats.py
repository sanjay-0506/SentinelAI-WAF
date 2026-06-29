from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.repositories.processed_log_repo import ProcessedLogRepository
from app.schemas.stats import RecentBlockedEntry, StatsResponse
from app.services.cache_service import CacheService

logger = get_logger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "",
    response_model=StatsResponse,
    summary="Dashboard statistics",
    description=(
        "Returns aggregate WAF statistics. "
        "Results are Redis-cached for 5 seconds to reduce DB load."
    ),
)
async def get_stats(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StatsResponse:
    cache = CacheService()
    settings = request.app.state.settings

    # Try Redis cache first
    cached = await cache.get_stats()
    if cached:
        logger.debug("stats.cache_hit")
        return StatsResponse(**cached)

    # Cache miss — query database
    repo = ProcessedLogRepository(db)

    aggregate = await repo.get_stats()
    attack_breakdown = await repo.get_attack_breakdown()
    recent_rows = await repo.get_recent(limit=10)

    recent_blocked: list[RecentBlockedEntry] = []
    for processed, raw in recent_rows:
        recent_blocked.append(
            RecentBlockedEntry(
                request_id=str(raw.id),
                ip_address=str(raw.ip_address),
                method=raw.method,
                path=raw.path,
                attack_type=processed.attack_type,
                severity=None,  # not stored on ProcessedRequestLog directly
                created_at=processed.created_at,
            )
        )

    stats = StatsResponse(
        total_requests=aggregate["total_requests"],
        blocked=aggregate["blocked"],
        allowed=aggregate["allowed"],
        block_rate=aggregate["block_rate"],
        attack_breakdown=attack_breakdown,
        recent_blocked=recent_blocked,
        generated_at=datetime.now(timezone.utc),
    )

    # Store in cache
    await cache.set_stats(
        stats.model_dump(mode="json"),
        ttl=settings.stats_cache_ttl,
    )

    return stats
