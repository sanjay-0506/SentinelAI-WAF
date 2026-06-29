import json
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_RATE_LIMIT_KEY_PREFIX = "rate_limit"


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter implemented with Redis INCR + EXPIRE.

    Each client IP gets a counter key in Redis with a 60-second TTL.  On the
    first request the counter is set to 1 and the TTL is applied.  Subsequent
    requests within the window increment the counter atomically.  When the
    counter exceeds ``limit_per_minute`` a 429 JSON response is returned.

    Fail-open behaviour: if Redis is unavailable the middleware logs the error
    and forwards the request normally to avoid service disruption.
    """

    def __init__(self, app, limit_per_minute: int = 100) -> None:
        super().__init__(app)
        self.limit = limit_per_minute
        self.window_seconds = 60

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip = self._get_client_ip(request)
        redis_key = f"{_RATE_LIMIT_KEY_PREFIX}:{ip}"

        try:
            from app.core.redis_client import get_redis

            r = get_redis()
            count = await r.incr(redis_key)
            if count == 1:
                # First hit in this window — set the expiry
                await r.expire(redis_key, self.window_seconds)

            if count > self.limit:
                logger.warning(
                    "rate_limit.exceeded",
                    ip=ip,
                    count=count,
                    limit=self.limit,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "detail": (
                            f"Too many requests. Limit is {self.limit} "
                            f"requests per {self.window_seconds} seconds."
                        ),
                        "retry_after_seconds": self.window_seconds,
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )
        except RuntimeError:
            # Redis not yet initialised (e.g. during startup)
            logger.debug("rate_limiter.redis_unavailable", ip=ip)
        except Exception as exc:  # noqa: BLE001
            # Fail open — do not block requests when Redis is down
            logger.error("rate_limiter.redis_error", ip=ip, error=str(exc))

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "unknown"
