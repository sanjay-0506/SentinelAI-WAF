import math
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processed_request_log import ProcessedRequestLog
from app.models.raw_request_log import RawRequestLog


class ProcessedLogRepository:
    """Data-access layer for processed request logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        raw_log_id: str | uuid.UUID,
        normalized_path: str,
        normalized_body: str | None,
        fingerprint: str,
        decision: str,
        attack_type: str | None,
        rule_version: str | None,
        response_status: int | None,
        latency_ms: float | None,
    ) -> ProcessedRequestLog:
        """Persist a new processed log entry."""
        log = ProcessedRequestLog(
            raw_log_id=raw_log_id,
            normalized_path=normalized_path,
            normalized_body=normalized_body,
            fingerprint=fingerprint,
            decision=decision,
            attack_type=attack_type,
            rule_version=rule_version,
            response_status=response_status,
            latency_ms=latency_ms,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        decision: str | None = None,
        attack_type: str | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list, int]:
        """Return a page of processed logs joined with raw logs and total count.

        Returns:
            Tuple of (rows, total_count) where rows are ORM objects.
        """
        # Count query
        count_stmt = select(func.count()).select_from(ProcessedRequestLog)
        data_stmt = (
            select(ProcessedRequestLog, RawRequestLog)
            .join(
                RawRequestLog,
                ProcessedRequestLog.raw_log_id == RawRequestLog.id,
            )
        )

        # Apply filters
        if decision:
            count_stmt = count_stmt.where(
                ProcessedRequestLog.decision == decision
            )
            data_stmt = data_stmt.where(
                ProcessedRequestLog.decision == decision
            )
        if attack_type:
            count_stmt = count_stmt.where(
                ProcessedRequestLog.attack_type == attack_type
            )
            data_stmt = data_stmt.where(
                ProcessedRequestLog.attack_type == attack_type
            )
        if ip_address:
            count_stmt = count_stmt.join(
                RawRequestLog,
                ProcessedRequestLog.raw_log_id == RawRequestLog.id,
            ).where(RawRequestLog.ip_address == ip_address)
            data_stmt = data_stmt.where(
                RawRequestLog.ip_address == ip_address
            )
        if start_date:
            count_stmt = count_stmt.where(
                ProcessedRequestLog.created_at >= start_date
            )
            data_stmt = data_stmt.where(
                ProcessedRequestLog.created_at >= start_date
            )
        if end_date:
            count_stmt = count_stmt.where(
                ProcessedRequestLog.created_at <= end_date
            )
            data_stmt = data_stmt.where(
                ProcessedRequestLog.created_at <= end_date
            )

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        data_stmt = (
            data_stmt.order_by(ProcessedRequestLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        data_result = await self._session.execute(data_stmt)
        rows = data_result.all()

        return rows, total

    async def get_stats(self) -> dict:
        """Return aggregate request stats: total, blocked, allowed."""
        stmt = select(
            func.count().label("total"),
            func.count()
            .filter(ProcessedRequestLog.decision == "blocked")
            .label("blocked"),
            func.count()
            .filter(ProcessedRequestLog.decision == "allowed")
            .label("allowed"),
        )
        result = await self._session.execute(stmt)
        row = result.one()
        total = row.total or 0
        blocked = row.blocked or 0
        allowed = row.allowed or 0
        block_rate = blocked / total if total > 0 else 0.0
        return {
            "total_requests": total,
            "blocked": blocked,
            "allowed": allowed,
            "block_rate": round(block_rate, 4),
        }

    async def get_attack_breakdown(self) -> dict[str, int]:
        """Return per-attack-category counts for blocked requests."""
        stmt = (
            select(
                ProcessedRequestLog.attack_type,
                func.count().label("count"),
            )
            .where(ProcessedRequestLog.attack_type.isnot(None))
            .group_by(ProcessedRequestLog.attack_type)
        )
        result = await self._session.execute(stmt)
        return {row.attack_type: row.count for row in result.all()}

    async def get_latency_percentiles(self) -> dict[str, float]:
        """Return approximate p50/p95/p99 latency from stored values."""
        stmt = select(ProcessedRequestLog.latency_ms).where(
            ProcessedRequestLog.latency_ms.isnot(None)
        )
        result = await self._session.execute(stmt)
        raw = [row[0] for row in result.all()]
        if not raw:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        latencies = sorted(raw)
        n = len(latencies)
        return {
            "p50": latencies[min(int(n * 0.50), n - 1)],
            "p95": latencies[min(int(n * 0.95), n - 1)],
            "p99": latencies[min(int(n * 0.99), n - 1)],
        }

    async def get_recent(self, limit: int = 10) -> list:
        """Return the most recent blocked requests."""
        stmt = (
            select(ProcessedRequestLog, RawRequestLog)
            .join(
                RawRequestLog,
                ProcessedRequestLog.raw_log_id == RawRequestLog.id,
            )
            .where(ProcessedRequestLog.decision == "blocked")
            .order_by(ProcessedRequestLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.all()
