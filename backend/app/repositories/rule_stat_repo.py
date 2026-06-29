from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule_stat import RuleStat


class RuleStatRepository:
    """Data-access layer for :class:`~app.models.rule_stat.RuleStat`.

    Provides atomic upsert-based increment so concurrent workers don't
    race on the counter value.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def increment(
        self,
        rule_id: str,
        rule_name: str,
        category: str,
        severity: str,
    ) -> None:
        """Atomically increment the hit_count for ``rule_id``.

        Inserts a new row with ``hit_count=1`` on first hit, or increments
        the existing counter using PostgreSQL's ``ON CONFLICT DO UPDATE``.

        Args:
            rule_id: Machine-readable rule identifier (e.g. ``'SQLI_001'``).
            rule_name: Human-readable rule name.
            category: Attack category string.
            severity: Severity string.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            pg_insert(RuleStat)
            .values(
                rule_id=rule_id,
                rule_name=rule_name,
                category=category,
                severity=severity,
                hit_count=1,
                last_triggered_at=now,
            )
            .on_conflict_do_update(
                index_elements=["rule_id"],
                set_={
                    RuleStat.hit_count: RuleStat.hit_count + 1,
                    RuleStat.last_triggered_at: now,
                    RuleStat.updated_at: now,
                },
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_top_rules(self, limit: int = 10) -> list[RuleStat]:
        """Return the top ``limit`` rules ordered by hit_count descending.

        Args:
            limit: Maximum number of rules to return.

        Returns:
            List of :class:`RuleStat` ORM objects.
        """
        stmt = (
            select(RuleStat)
            .order_by(RuleStat.hit_count.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self) -> list[RuleStat]:
        """Return all rule stats ordered by hit_count descending."""
        stmt = select(RuleStat).order_by(RuleStat.hit_count.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_rule_id(self, rule_id: str) -> RuleStat | None:
        """Fetch a single rule stat by rule_id."""
        stmt = select(RuleStat).where(RuleStat.rule_id == rule_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
