import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from app.core.database import Base

engine_enum = Enum("rule_engine", "secbert", "autoencoder", "meta_learner", name="engine_enum", create_type=False)
decision_enum = Enum("allowed", "blocked", name="decision_enum", create_type=False)
severity_enum = Enum(
    "LOW", "MEDIUM", "HIGH", "CRITICAL",
    name="severity_enum",
    create_type=False,
)


class DetectionResultModel(Base):
    """Stores per-engine detection outcomes for a single request.

    Multiple rows can exist per request (one per engine that fires).
    Currently only the ``rule_engine`` engine is implemented; classifier and
    anomaly engines are reserved for Level-2 expansion.
    """

    __tablename__ = "detection_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    raw_log_id: Mapped[uuid.UUID] = mapped_column(
        "request_id",
        UUID(as_uuid=True),
        ForeignKey("raw_request_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engine: Mapped[str] = mapped_column(engine_enum, nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    severity: Mapped[str | None] = mapped_column(severity_enum, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(decision_enum, nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    raw_log: Mapped["RawRequestLog"] = relationship(  # type: ignore[name-defined]
        "RawRequestLog",
        back_populates="detection_results",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<DetectionResultModel id={self.id} engine={self.engine} "
            f"decision={self.decision} rule_id={self.rule_id}>"
        )
