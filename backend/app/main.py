import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import health, inspect, logs, metrics, rules, stats
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.logging_config import configure_logging, get_logger
from app.core.redis_client import close_redis, init_redis
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_size import RequestSizeMiddleware
from app.normalization.normalizer import NormalizerService
from app.rules.engine import RuleEngine
from app.services.proxy_service import ProxyService

logger = get_logger(__name__)

_RULES_YAML_PATH = Path(__file__).parent / "rules" / "rules.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Startup:
    - Configure structured logging
    - Initialise PostgreSQL connection pool
    - Initialise Redis connection
    - Load WAF rules into RuleEngine singleton
    - Create NormalizerService and ProxyService singletons

    Shutdown:
    - Close DB pool
    - Close Redis connection
    - Close ProxyService HTTP client
    """
    settings = get_settings()
    configure_logging(log_level="DEBUG" if settings.debug else "INFO")

    logger.info("startup.begin", app=settings.app_name, version=settings.app_version)

    # PostgreSQL
    await init_db(settings.database_url)
    logger.info("startup.postgres_connected")

    # Redis
    try:
        await init_redis(settings.redis_url)
        logger.info("startup.redis_connected")
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup.redis_unavailable", error=str(exc))

    # Rule engine
    rule_engine = RuleEngine()
    rule_engine.load_rules(_RULES_YAML_PATH)
    logger.info(
        "startup.rules_loaded",
        count=rule_engine.rules_loaded,
        version=rule_engine.ruleset_version,
    )

    # Singletons stored in app.state
    app.state.settings = settings
    app.state.rule_engine = rule_engine
    app.state.normalizer = NormalizerService()
    app.state.proxy_service = ProxyService(
        juice_shop_url=settings.juice_shop_url,
        dvwa_url=settings.dvwa_url,
    )
    app.state.start_time = time.monotonic()

    logger.info("startup.complete")
    yield  # ──── application is running ────

    # Shutdown
    logger.info("shutdown.begin")
    await app.state.proxy_service.close()
    await close_redis()
    await close_db()
    logger.info("shutdown.complete")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="AI-WAF Gateway",
        version="1.0.0",
        description=(
            "AI-powered Web Application Firewall with rule-based detection, "
            "async proxy, and extensible ML engine interfaces."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────
    allowed_origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom middleware (outermost → innermost) ─────────────────────────
    app.add_middleware(
        RequestSizeMiddleware,
        max_size_mb=settings.max_request_size_mb,
    )
    app.add_middleware(
        RateLimiterMiddleware,
        limit_per_minute=settings.rate_limit_per_minute,
    )

    from app.api.v1 import health, inspect, logs, metrics, rules, stats, proxy

    # ── Routers ──────────────────────────────────────────────────────────
    _API_PREFIX = "/api/v1"
    app.include_router(inspect.router, prefix=_API_PREFIX)
    app.include_router(stats.router, prefix=_API_PREFIX)
    app.include_router(logs.router, prefix=_API_PREFIX)
    app.include_router(rules.router, prefix=_API_PREFIX)
    app.include_router(health.router, prefix=_API_PREFIX)
    app.include_router(metrics.router, prefix=_API_PREFIX)
    
    # Register proxy router at root proxy level to handle /proxy/{target}
    app.include_router(proxy.router, prefix="/proxy")

    # ── Global exception handler ──────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected error occurred. Please try again later.",
            },
        )

    return app


app = create_app()
