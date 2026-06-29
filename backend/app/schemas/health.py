from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response for the GET /health endpoint."""

    status: str = Field(
        description="Overall service health: 'healthy', 'degraded', or 'unhealthy'."
    )
    postgres: str = Field(description="PostgreSQL connectivity: 'up' or 'down'.")
    redis: str = Field(description="Redis connectivity: 'up' or 'down'.")
    rules_loaded: int = Field(description="Number of WAF rules currently loaded.")
    ruleset_version: str = Field(description="Version string of the active ruleset.")
    version: str = Field(description="Application version string.")
    uptime_seconds: float = Field(
        description="Seconds elapsed since the application started.", ge=0.0
    )
