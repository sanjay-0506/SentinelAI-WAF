from datetime import datetime

from pydantic import BaseModel, Field


class RecentBlockedEntry(BaseModel):
    """Summary of a recently blocked request for the dashboard."""

    request_id: str
    ip_address: str
    method: str
    path: str
    attack_type: str | None = None
    severity: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    """Dashboard statistics response for the GET /stats endpoint."""

    total_requests: int = Field(
        description="Total number of requests processed since startup."
    )
    blocked: int = Field(description="Number of requests blocked by the WAF.")
    allowed: int = Field(description="Number of requests passed through.")
    block_rate: float = Field(
        description="Fraction of requests blocked (0.0 – 1.0).", ge=0.0, le=1.0
    )
    attack_breakdown: dict[str, int] = Field(
        description="Per-category attack counts, e.g. {'SQLI': 42, 'XSS': 10}."
    )
    recent_blocked: list[RecentBlockedEntry] = Field(
        default_factory=list,
        description="The most recent blocked requests (up to 10).",
    )
    generated_at: datetime = Field(
        description="UTC timestamp when these stats were generated."
    )
