"""Pytest fixtures shared across the test suite."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.normalization.normalizer import NormalizerService
from app.rules.engine import RuleEngine

_RULES_YAML = Path(__file__).parent.parent / "app" / "rules" / "rules.yaml"


@pytest.fixture(scope="session")
def normalizer() -> NormalizerService:
    """Return a shared NormalizerService instance for the test session."""
    return NormalizerService()


@pytest.fixture(scope="session")
def rule_engine() -> RuleEngine:
    """Return a RuleEngine loaded with the production rules.yaml."""
    engine = RuleEngine()
    engine.load_rules(_RULES_YAML)
    return engine


@pytest.fixture
def test_client() -> TestClient:
    """Return a FastAPI TestClient with DB and Redis mocked out.

    The client bypasses the real lifespan startup/shutdown; instead it
    patches the database session, Redis client, and pre-seeds app.state
    with the real RuleEngine and a NormalizerService so endpoint logic
    can run without external dependencies.
    """
    from app.main import create_app

    application = create_app()

    # Pre-seed app state (normally done in lifespan)
    engine = RuleEngine()
    engine.load_rules(_RULES_YAML)
    application.state.rule_engine = engine
    application.state.normalizer = NormalizerService()

    # Mock proxy service
    mock_proxy = MagicMock()
    mock_proxy.forward = AsyncMock(
        return_value={"status": 200, "body": b"OK", "headers": {}}
    )
    mock_proxy.close = AsyncMock()
    application.state.proxy_service = mock_proxy

    from app.core.config import get_settings
    application.state.settings = get_settings()

    import time
    application.state.start_time = time.monotonic()

    # Patch DB dependency to return a mock session
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    async def _mock_get_db():
        yield mock_session

    from app.core import database as db_module
    db_module.AsyncSessionFactory = MagicMock(return_value=mock_session)

    # Patch Redis to avoid connection errors in middleware
    with patch("app.core.redis_client._redis_client", new=AsyncMock()) as mock_redis:
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.zadd = AsyncMock(return_value=1)
        mock_redis.zremrangebyrank = AsyncMock(return_value=0)
        mock_redis.zrange = AsyncMock(return_value=[])

        with TestClient(application, raise_server_exceptions=True) as client:
            yield client
