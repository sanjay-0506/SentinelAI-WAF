from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.replay_repo import ReplayRepository


class ReplayService:
    """Service for queueing and managing request replays.

    Replays feed the Level-2 AI/ML training pipeline and allow post-incident
    forensic re-evaluation of flagged requests.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ReplayRepository(session)

    async def enqueue(
        self,
        request_log_id: str,
        payload: str,
        headers: dict,
        method: str,
        path: str,
    ) -> str:
        """Queue a blocked request for future Level-2 replay / training.

        Args:
            request_log_id: UUID of the associated RawRequestLog entry.
            payload: Raw or normalised request body payload.
            headers: Request headers dict to persist with the replay.
            method: HTTP method of the original request.
            path: URL path of the original request.

        Returns:
            String UUID of the created RequestReplay record.
        """
        replay = await self._repo.enqueue(
            request_log_id=request_log_id,
            payload=payload,
            headers=headers,
            method=method,
            path=path,
        )
        return str(replay.id)

    async def get_pending(self, limit: int = 100) -> list:
        """Return up to ``limit`` pending replay records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of :class:`~app.models.request_replay.RequestReplay` ORM
            objects with ``status == 'pending'``.
        """
        return await self._repo.get_pending(limit)

    async def mark_replayed(self, replay_id: str) -> None:
        """Mark a replay record as successfully replayed."""
        await self._repo.mark_replayed(replay_id)

    async def mark_failed(self, replay_id: str) -> None:
        """Mark a replay record as failed."""
        await self._repo.mark_failed(replay_id)
