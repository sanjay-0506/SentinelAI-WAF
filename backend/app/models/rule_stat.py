import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func, text

from app.core.database import Base

rule_category_enum = Enum(
    "SQLI",
    "XSS",
    "PATH_TRAVERSAL",
    "COMMAND_INJECTION",
    name="attack_category_enum",
    create_type=False,
)
rule_severity_stat_enum = Enum(
    "LOW", "MEDIUM", "HIGH", "CRITICAL",
    name="severity_enum",
    create_type=False,
)


class RuleStat(Base):
    """Aggregated hit counter for each WAF rule.

    Updated via upsert (INSERT … ON CONFLICT DO UPDATE) so only one row
    exists per rule_id.  Used to display hit counts on the /rules endpoint
    and to surface the most triggered rules in dashboards.
    """

    __tablename__ = "rule_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    rule_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(rule_category_enum, nullable=False, index=True)
    severity: Mapped[str] = mapped_column(rule_severity_stat_enum, nullable=False)
    hit_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        "last_triggered", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RuleStat rule_id={self.rule_id!r} hit_count={self.hit_count}>"
        )
