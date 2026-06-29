import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_request_log import RawRequestLog


class RawLogRepository:
    """Data-access layer for :class:`~app.models.raw_request_log.RawRequestLog`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        ip_address: str,
        method: str,
        path: str,
        headers: dict[str, Any],
        body: str | None,
        user_agent: str | None,
        request_size: int,
    ) -> RawRequestLog:
        """Persist a new raw request log entry and flush to obtain the PK.

        Args:
            ip_address: Client IP address string.
            method: HTTP method (GET, POST, …).
            path: Raw URL path.
            headers: Full HTTP headers dict.
            body: Raw request body string, or None.
            user_agent: Value of the User-Agent header, or None.
            request_size: Size of the request body in bytes.

        Returns:
            The persisted :class:`RawRequestLog` instance with ``id`` populated.
        """
        log = RawRequestLog(
            ip_address=ip_address,
            method=method,
            path=path,
            headers=headers,
            body=body,
            user_agent=user_agent,
            request_size=request_size,
        )
        self._session.add(log)
        await self._session.flush()  # populate server-generated UUID
        return log

    async def get_by_id(self, id: str | uuid.UUID) -> RawRequestLog | None:
        """Fetch a raw request log by its UUID primary key.

        Args:
            id: UUID string or object.

        Returns:
            The matching :class:`RawRequestLog`, or ``None`` if not found.
        """
        stmt = select(RawRequestLog).where(RawRequestLog.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
