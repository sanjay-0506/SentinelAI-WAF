from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_BYTES_PER_MB = 1024 * 1024


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured limit.

    Checks the ``Content-Length`` header before the request body is read.
    If the header is absent the request is allowed through — streaming
    payloads are the application's responsibility to bound.

    Returns HTTP 413 with a JSON body when the limit is exceeded.
    """

    def __init__(self, app, max_size_mb: int = 10) -> None:
        super().__init__(app)
        self.max_size_bytes = max_size_mb * _BYTES_PER_MB
        self.max_size_mb = max_size_mb

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "invalid_content_length",
                        "detail": "Content-Length header must be an integer.",
                    },
                )
            if size > self.max_size_bytes:
                logger.warning(
                    "request_size.exceeded",
                    content_length=size,
                    max_bytes=self.max_size_bytes,
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "request_too_large",
                        "detail": (
                            f"Request body exceeds the maximum allowed size "
                            f"of {self.max_size_mb} MB."
                        ),
                        "max_size_mb": self.max_size_mb,
                    },
                )
        return await call_next(request)
