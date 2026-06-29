from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI-WAF"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    max_request_size_mb: int = 10
    rate_limit_per_minute: int = 100

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "wafdb"
    postgres_user: str = "wafuser"
    postgres_password: str = "wafpassword"
    database_url: str = "postgresql+asyncpg://wafuser:wafpassword@localhost:5432/wafdb"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = "redis://localhost:6379/0"
    stats_cache_ttl: int = 5

    juice_shop_url: str = "http://localhost:3000"
    dvwa_url: str = "http://localhost:8080"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
