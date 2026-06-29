from pydantic import BaseModel, Field


class InspectRequest(BaseModel):
    """Payload for the POST /inspect endpoint."""

    method: str = Field(
        default="GET",
        description="HTTP method of the request being inspected.",
        examples=["GET", "POST"],
    )
    path: str = Field(
        description="URL path of the request.",
        examples=["/api/users"],
    )
    body: str = Field(
        default="",
        description="Raw request body as a string (may be empty).",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="HTTP request headers.",
    )
    ip_address: str = Field(
        default="127.0.0.1",
        description="Client IP address.",
        examples=["10.0.0.1"],
    )


class InspectResponse(BaseModel):
    """Response from the POST /inspect endpoint."""

    allowed: bool = Field(description="True if the request passes WAF checks.")
    attack_type: str | None = Field(
        default=None,
        description="Detected attack category (SQLI, XSS, …), or null if allowed.",
    )
    confidence: float = Field(
        description="Confidence score of the detection [0.0 – 1.0].",
        ge=0.0,
        le=1.0,
    )
    matched_rule: str | None = Field(
        default=None,
        description="Human-readable name of the matched rule, or null.",
    )
    rule_id: str | None = Field(
        default=None,
        description="Machine-readable ID of the matched rule (e.g. SQLI_001).",
    )
    severity: str | None = Field(
        default=None,
        description="Severity of the matched rule (LOW / MEDIUM / HIGH / CRITICAL).",
    )
    fingerprint: str = Field(
        description="SHA-256 fingerprint of the normalised request content.",
    )
    request_id: str = Field(
        description="UUID of the persisted RawRequestLog entry.",
    )
    latency_ms: float = Field(
        description="End-to-end detection latency in milliseconds.",
        ge=0.0,
    )
