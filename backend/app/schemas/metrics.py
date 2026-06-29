from pydantic import BaseModel, Field


class MetricsResponse(BaseModel):
    """Response for the GET /metrics endpoint."""

    requests_total: int = Field(
        description="Total requests processed since startup."
    )
    blocked_total: int = Field(description="Total requests blocked.")
    allowed_total: int = Field(description="Total requests allowed.")
    block_rate: float = Field(
        description="Fraction of requests blocked (0.0 – 1.0).", ge=0.0, le=1.0
    )
    sqli_total: int = Field(description="SQL injection detections.")
    xss_total: int = Field(description="Cross-site scripting detections.")
    path_traversal_total: int = Field(description="Path traversal detections.")
    command_injection_total: int = Field(description="Command injection detections.")
    latency_p50_ms: float = Field(
        description="50th percentile detection latency in milliseconds.", ge=0.0
    )
    latency_p95_ms: float = Field(
        description="95th percentile detection latency in milliseconds.", ge=0.0
    )
    latency_p99_ms: float = Field(
        description="99th percentile detection latency in milliseconds.", ge=0.0
    )
    uptime_seconds: float = Field(
        description="Seconds since the application started.", ge=0.0
    )
    rules_loaded: int = Field(description="Number of active WAF rules.")
