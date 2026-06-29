import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from app.core.database import Base


class RawRequestLog(Base):
    """Persists the raw, unmodified HTTP request before any WAF processing.

    Uses PostgreSQL UUID (uuid_generate_v4) as the primary key and JSONB for
    headers to allow efficient key-based querying.
    """

    __tablename__ = "raw_request_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    ip_address: Mapped[str] = mapped_column(
        INET,
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    headers: Mapped[dict] = mapped_column("original_headers", JSONB, nullable=False, default=dict)
    body: Mapped[str | None] = mapped_column("original_body", Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        "timestamp",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    processed_log: Mapped["ProcessedRequestLog"] = relationship(  # type: ignore[name-defined]
        "ProcessedRequestLog",
        back_populates="raw_log",
        uselist=False,
        lazy="select",
    )
    detection_results: Mapped[list["DetectionResultModel"]] = relationship(  # type: ignore[name-defined]
        "DetectionResultModel",
        back_populates="raw_log",
        lazy="select",
    )
    replays: Mapped[list["RequestReplay"]] = relationship(  # type: ignore[name-defined]
        "RequestReplay",
        back_populates="raw_log",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RawRequestLog id={self.id} method={self.method} path={self.path!r}>"
        )
