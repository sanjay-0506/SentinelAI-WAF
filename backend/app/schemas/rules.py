from pydantic import BaseModel, Field


class RuleEntry(BaseModel):
    """Representation of a single WAF rule with runtime hit statistics."""

    id: str = Field(description="Machine-readable rule ID (e.g. SQLI_001).")
    version: int = Field(description="Rule version number.")
    name: str = Field(description="Human-readable rule name.")
    severity: str = Field(description="Rule severity (LOW/MEDIUM/HIGH/CRITICAL).")
    priority: int = Field(description="Evaluation priority; lower = higher priority.")
    pattern: str = Field(description="Compiled regex pattern string.")
    category: str = Field(description="Attack category this rule belongs to.")
    description: str = Field(default="", description="Detailed rule description.")
    hit_count: int = Field(
        default=0,
        description="Number of times this rule has triggered since service start.",
    )


class RulesResponse(BaseModel):
    """Response for the GET /rules endpoint."""

    ruleset_version: str = Field(description="Version string of the loaded ruleset.")
    rules_loaded: int = Field(description="Total number of compiled rules.")
    rules: list[RuleEntry] = Field(description="All loaded rules with hit counts.")
