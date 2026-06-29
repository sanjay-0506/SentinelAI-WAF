from datetime import datetime

from pydantic import BaseModel, Field


class LogFilterParams(BaseModel):
    """Query-parameter model for filtering log results."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Results per page (max 100)."
    )
    decision: str | None = Field(
        default=None,
        description="Filter by WAF decision: 'allowed' or 'blocked'.",
    )
    attack_type: str | None = Field(
        default=None,
        description="Filter by attack category (SQLI, XSS, PATH_TRAVERSAL, COMMAND_INJECTION).",
    )
    ip_address: str | None = Field(
        default=None,
        description="Filter by exact client IP address.",
    )
    start_date: datetime | None = Field(
        default=None,
        description="Include only requests on or after this UTC datetime.",
    )
    end_date: datetime | None = Field(
        default=None,
        description="Include only requests on or before this UTC datetime.",
    )


class LogEntry(BaseModel):
    """Single log entry combining raw and processed request data."""

    request_id: str = Field(description="UUID of the RawRequestLog entry.")
    ip_address: str
    method: str
    path: str
    decision: str
    attack_type: str | None = None
    severity: str | None = None
    confidence: float | None = None
    fingerprint: str | None = None
    latency_ms: float | None = None
    user_agent: str | None = None
    request_size: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogsResponse(BaseModel):
    """Paginated response for the GET /logs endpoint."""

    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[LogEntry]
