import math
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.repositories.processed_log_repo import ProcessedLogRepository
from app.schemas.logs import LogEntry, LogFilterParams, LogsResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get(
    "",
    response_model=LogsResponse,
    summary="Paginated request logs",
    description=(
        "Return paginated WAF request logs with optional filters for "
        "decision, attack_type, ip_address, and date range."
    ),
)
async def get_logs(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Results per page (max 100)."
    ),
    decision: str | None = Query(
        default=None,
        description="Filter by WAF decision: 'allowed' or 'blocked'.",
    ),
    attack_type: str | None = Query(
        default=None,
        description="Attack category filter (SQLI, XSS, PATH_TRAVERSAL, COMMAND_INJECTION).",
    ),
    ip_address: str | None = Query(
        default=None,
        description="Filter by exact client IP address.",
    ),
    start_date: datetime | None = Query(
        default=None,
        description="Include requests on or after this UTC datetime (ISO 8601).",
    ),
    end_date: datetime | None = Query(
        default=None,
        description="Include requests on or before this UTC datetime (ISO 8601).",
    ),
) -> LogsResponse:
    repo = ProcessedLogRepository(db)

    rows, total = await repo.get_paginated(
        page=page,
        page_size=page_size,
        decision=decision,
        attack_type=attack_type,
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date,
    )

    items: list[LogEntry] = []
    for processed, raw in rows:
        items.append(
            LogEntry(
                request_id=str(raw.id),
                ip_address=str(raw.ip_address),
                method=raw.method,
                path=raw.path,
                decision=processed.decision,
                attack_type=processed.attack_type,
                severity=None,
                confidence=None,
                fingerprint=processed.fingerprint,
                latency_ms=processed.latency_ms,
                user_agent=raw.user_agent,
                request_size=raw.request_size,
                created_at=processed.created_at,
            )
        )

    total_pages = max(1, math.ceil(total / page_size))

    return LogsResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=items,
    )
