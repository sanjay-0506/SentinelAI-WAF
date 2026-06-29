import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from app.core.database import Base

decision_enum = Enum("allowed", "blocked", name="decision_enum", create_type=False)
attack_type_enum = Enum(
    "SQLI",
    "XSS",
    "PATH_TRAVERSAL",
    "COMMAND_INJECTION",
    name="attack_category_enum",
    create_type=False,
)


class ProcessedRequestLog(Base):
    """Persists the WAF's normalised view and verdict for each request.

    Linked 1-to-1 with :class:`~app.models.raw_request_log.RawRequestLog`.
    """

    __tablename__ = "processed_request_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    raw_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_request_logs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    normalized_path: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(
        decision_enum,
        nullable=False,
        index=True,
    )
    attack_type: Mapped[str | None] = mapped_column(
        attack_type_enum,
        nullable=True,
        index=True,
    )
    rule_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    raw_log: Mapped["RawRequestLog"] = relationship(  # type: ignore[name-defined]
        "RawRequestLog",
        back_populates="processed_log",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ProcessedRequestLog id={self.id} decision={self.decision} "
            f"attack_type={self.attack_type}>"
        )
