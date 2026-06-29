import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection_result import DetectionResultModel


class DetectionResultRepository:
    """Data-access layer for per-engine detection results."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        request_id: str | uuid.UUID,
        engine: str,
        rule_id: str | None,
        severity: str | None,
        confidence: float,
        decision: str,
        matched_pattern: str | None = None,
        metadata: dict | None = None,
    ) -> DetectionResultModel:
        """Persist a detection result for a single engine evaluation.

        Args:
            request_id: UUID of the associated RawRequestLog.
            engine: Detection engine name ('rule_engine', 'classifier', …).
            rule_id: Matched rule ID, or None if no rule fired.
            severity: Severity string, or None.
            confidence: Confidence score [0.0 – 1.0].
            decision: 'allow' or 'block'.
            matched_pattern: Substring that triggered the match, or None.
            metadata: Arbitrary extra data dict.

        Returns:
            The persisted :class:`DetectionResultModel` instance.
        """
        if matched_pattern:
            metadata = metadata or {}
            metadata["matched_pattern"] = matched_pattern
            
        record = DetectionResultModel(
            raw_log_id=request_id,
            engine=engine,
            rule_id=rule_id,
            severity=severity,
            confidence=confidence,
            decision=decision,
            metadata_=metadata or {},
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_request(
        self, request_id: str | uuid.UUID
    ) -> list[DetectionResultModel]:
        """Return all detection results associated with a given request ID.

        Args:
            request_id: UUID of the target RawRequestLog.

        Returns:
            Ordered list of :class:`DetectionResultModel` rows.
        """
        stmt = (
            select(DetectionResultModel)
            .where(DetectionResultModel.raw_log_id == request_id)
            .order_by(DetectionResultModel.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
