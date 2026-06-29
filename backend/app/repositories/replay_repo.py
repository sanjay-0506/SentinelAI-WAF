import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_replay import RequestReplay


class ReplayRepository:
    """Data-access layer for :class:`~app.models.request_replay.RequestReplay`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        request_log_id: str | uuid.UUID,
        payload: str | None,
        headers: dict,
        method: str,
        path: str,
    ) -> RequestReplay:
        """Insert a new replay record with ``status='pending'``.

        Args:
            request_log_id: UUID of the associated RawRequestLog.
            payload: Raw or normalised request body to replay.
            headers: Headers dict to persist alongside the replay.
            method: HTTP method of the original request.
            path: URL path of the original request.

        Returns:
            The persisted :class:`RequestReplay` instance.
        """
        replay = RequestReplay(
            raw_log_id=request_log_id,
            payload=payload,
            headers=headers,
            method=method,
            path=path,
            status="pending",
        )
        self._session.add(replay)
        await self._session.flush()
        return replay

    async def get_pending(self, limit: int = 100) -> list[RequestReplay]:
        """Return up to ``limit`` pending replay records ordered by creation time.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of :class:`RequestReplay` with ``status == 'pending'``.
        """
        stmt = (
            select(RequestReplay)
            .where(RequestReplay.status == "pending")
            .order_by(RequestReplay.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_replayed(self, replay_id: str | uuid.UUID) -> None:
        """Update a replay record to ``status='replayed'`` with a timestamp."""
        replay = await self._get_by_id(replay_id)
        if replay:
            replay.status = "replayed"
            replay.replayed_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def mark_failed(self, replay_id: str | uuid.UUID) -> None:
        """Update a replay record to ``status='failed'``."""
        replay = await self._get_by_id(replay_id)
        if replay:
            replay.status = "failed"
            await self._session.flush()

    async def _get_by_id(
        self, replay_id: str | uuid.UUID
    ) -> RequestReplay | None:
        stmt = select(RequestReplay).where(RequestReplay.id == replay_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
