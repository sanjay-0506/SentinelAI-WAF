from typing import Any
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Resolve the real client IP from request headers or connection info.

    Checks headers in order of trustworthiness:
    1. ``X-Forwarded-For`` — set by load balancers / reverse proxies.
       Takes the first (leftmost) IP which is the original client.
    2. ``X-Real-IP`` — set by Nginx and similar proxies.
    3. ``request.client.host`` — the raw TCP connection source IP.
    4. Falls back to ``"unknown"`` if none are available.

    Args:
        request: The incoming Starlette/FastAPI request object.

    Returns:
        A string IP address.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated list; first is the client
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client is not None:
        return request.client.host

    return "unknown"


def sanitize_null_bytes(val: Any) -> Any:
    """Recursively replace null bytes with literal string representations to prevent PostgreSQL insertion errors."""
    from typing import Dict, List
    if isinstance(val, str):
        return val.replace("\x00", "\\x00")
    elif isinstance(val, dict):
        return {k: sanitize_null_bytes(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_null_bytes(v) for v in val]
    return val
