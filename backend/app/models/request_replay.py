import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from app.core.database import Base

replay_status_enum = Enum(
    "pending", "replayed", "failed",
    name="replay_status_enum",
    create_type=False,
)


class RequestReplay(Base):
    """Queue of blocked requests for Level-2 replay and training data generation.

    Rows are inserted for every blocked request and consumed by an offline
    worker that re-evaluates them against newer ML models or feeds them into
    labelled training datasets.
    """

    __tablename__ = "request_replays"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    raw_log_id: Mapped[uuid.UUID] = mapped_column(
        "request_log_id",
        UUID(as_uuid=True),
        ForeignKey("raw_request_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        replay_status_enum,
        nullable=False,
        default="pending",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "timestamp",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    replayed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    raw_log: Mapped["RawRequestLog"] = relationship(  # type: ignore[name-defined]
        "RawRequestLog",
        back_populates="replays",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RequestReplay id={self.id} status={self.status} "
            f"path={self.path!r}>"
        )
