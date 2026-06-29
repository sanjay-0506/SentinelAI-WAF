from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.repositories.rule_stat_repo import RuleStatRepository
from app.rules.engine import RuleEngine
from app.schemas.rules import RuleEntry, RulesResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get(
    "",
    response_model=RulesResponse,
    summary="List all active WAF rules",
    description=(
        "Returns all currently loaded WAF rules merged with their "
        "hit counts from the database."
    ),
)
async def get_rules(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RulesResponse:
    rule_engine: RuleEngine = request.app.state.rule_engine
    rules = rule_engine.get_rules()

    # Build a hit_count lookup from DB
    rule_stat_repo = RuleStatRepository(db)
    all_stats = await rule_stat_repo.get_all()
    hit_count_map: dict[str, int] = {stat.rule_id: stat.hit_count for stat in all_stats}

    entries: list[RuleEntry] = [
        RuleEntry(
            id=rule.id,
            version=rule.version,
            name=rule.name,
            severity=rule.severity.value,
            priority=rule.priority,
            pattern=rule.pattern,
            category=rule.category.value,
            description=rule.description,
            hit_count=hit_count_map.get(rule.id, 0),
        )
        for rule in rules
    ]

    return RulesResponse(
        ruleset_version=rule_engine.ruleset_version,
        rules_loaded=rule_engine.rules_loaded,
        rules=entries,
    )
