import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import Rule, RuleSet, Severity


@dataclass
class DetectionResult:
    allowed: bool
    attack_type: str | None
    confidence: float
    matched_rule: str | None
    rule_id: str | None
    severity: str | None
    matched_pattern: str | None
    metadata: dict = field(default_factory=dict)


_CONFIDENCE_MAP: dict[Severity, float] = {
    Severity.CRITICAL: 0.95,
    Severity.HIGH: 0.85,
    Severity.MEDIUM: 0.70,
    Severity.LOW: 0.55,
}

_SHORT_CIRCUIT_SEVERITIES: frozenset[Severity] = frozenset(
    {Severity.CRITICAL, Severity.HIGH}
)


class RuleEngine:
    """Regex-based WAF rule engine.

    Rules are loaded from a YAML file, compiled into ``re.Pattern`` objects,
    and sorted by ascending priority so higher-priority rules are evaluated
    first.  The engine short-circuits on the first CRITICAL or HIGH match.
    """

    def __init__(self) -> None:
        self._rules: list[tuple[Rule, re.Pattern[str]]] = []
        self._ruleset_version: str = "unknown"
        self._rules_loaded: int = 0

    @property
    def ruleset_version(self) -> str:
        return self._ruleset_version

    @property
    def rules_loaded(self) -> int:
        return self._rules_loaded

    def load_rules(self, path: Path | str) -> None:
        """Load and compile rules from a YAML file."""
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        ruleset = RuleSet(**data)
        self._ruleset_version = ruleset.version
        compiled: list[tuple[Rule, re.Pattern[str]]] = []
        for rule in ruleset.rules:
            pattern = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
            compiled.append((rule, pattern))
        # Sort ascending by priority (lower number = higher priority)
        compiled.sort(key=lambda item: item[0].priority)
        self._rules = compiled
        self._rules_loaded = len(compiled)

    def evaluate(
        self,
        path: str,
        body: str,
        headers: dict[str, str],
    ) -> DetectionResult:
        """Evaluate a normalised request against all loaded rules.

        The combined target string is ``{path} {body} {header_values}``.
        Evaluation short-circuits on the first CRITICAL or HIGH match; for
        MEDIUM/LOW it also returns immediately on the first match (rules are
        already ordered by priority).
        """
        header_values = " ".join(str(v) for v in headers.values())
        combined = f"{path} {body} {header_values}"

        for rule, pattern in self._rules:
            match = pattern.search(combined)
            if match is not None:
                confidence = _CONFIDENCE_MAP.get(rule.severity, 0.70)
                return DetectionResult(
                    allowed=False,
                    attack_type=rule.category.value,
                    confidence=confidence,
                    matched_rule=rule.name,
                    rule_id=rule.id,
                    severity=rule.severity.value,
                    matched_pattern=match.group(0)[:100],
                    metadata={
                        "matched_at": match.start(),
                        "groups": list(match.groups()),
                        "priority": rule.priority,
                    },
                )

        return DetectionResult(
            allowed=True,
            attack_type=None,
            confidence=1.0,
            matched_rule=None,
            rule_id=None,
            severity=None,
            matched_pattern=None,
            metadata={},
        )

    def get_rules(self) -> list[Rule]:
        """Return all loaded Rule objects (in priority order)."""
        return [rule for rule, _ in self._rules]

    def get_match_details(self, text: str, rule_id: str) -> dict:
        """Return regex match details for a specific rule against the given text."""
        for rule, pattern in self._rules:
            if rule.id == rule_id:
                m = pattern.search(text)
                if m:
                    return {
                        "matched": m.group(0),
                        "start": m.start(),
                        "end": m.end(),
                        "groups": list(m.groups()),
                    }
        return {}
