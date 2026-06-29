import httpx

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_HOP_BY_HOP_HEADERS: frozenset[str] = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",
    }
)


class ProxyService:
    """Async reverse-proxy using httpx.

    Routes requests to OWASP Juice Shop (``/juice-shop`` prefix) or DVWA
    (``/dvwa`` prefix).  Hop-by-hop headers are stripped before forwarding.
    """

    def __init__(self, juice_shop_url: str, dvwa_url: str) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )
        self.juice_shop_url = juice_shop_url.rstrip("/")
        self.dvwa_url = dvwa_url.rstrip("/")

    async def forward_request(
        self,
        target: str,
        path: str,
        method: str,
        headers: dict[str, str],
        body: bytes,
        query_string: bytes = b"",
    ) -> httpx.Response:
        """Forward the request to the appropriate upstream target.

        Args:
            target: Upstream target name (e.g. ``juice-shop``, ``dvwa``).
            path: Request path without the target prefix.
            method: HTTP method string (e.g. ``"GET"``).
            headers: HTTP headers dict.
            body: Raw request body bytes.
            query_string: Raw query string bytes.

        Returns:
            An httpx.Response object from the upstream server.
        """
        target_base: str | None = None

        if target == "juice-shop":
            target_base = self.juice_shop_url
        elif target == "dvwa":
            target_base = self.dvwa_url
        else:
            logger.debug("proxy.no_target", target=target, path=path)
            return httpx.Response(status_code=404, content=b"Target not found")

        # Construct full upstream URL
        url = target_base + path
        if query_string:
            url += "?" + query_string.decode("utf-8")

        # Strip hop-by-hop headers before forwarding
        forward_headers = {
            k: v
            for k, v in headers.items()
            if k.lower() not in _HOP_BY_HOP_HEADERS
        }

        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=forward_headers,
                content=body,
            )
            logger.info(
                "proxy.forwarded",
                method=method,
                target=url,
                status=response.status_code,
            )
            return response
        except httpx.TimeoutException as exc:
            logger.error("proxy.timeout", target=url, error=str(exc))
            return httpx.Response(status_code=504, content=b"Gateway Timeout")
        except httpx.RequestError as exc:
            logger.error("proxy.error", target=url, error=str(exc))
            return httpx.Response(status_code=502, content=b"Bad Gateway")

    async def close(self) -> None:
        """Gracefully close the underlying httpx client."""
        await self._client.aclose()
