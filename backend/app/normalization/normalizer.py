import re
import unicodedata
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import unquote_plus

MAX_DECODE_DEPTH = 3


@dataclass
class NormalizedRequest:
    original_path: str
    normalized_path: str
    original_body: str
    normalized_body: str
    normalized_headers: dict[str, str]
    decode_depth: int = 0


class NormalizerService:
    """Normalises raw HTTP request data before rule evaluation.

    Performs iterative URL-decoding (up to MAX_DECODE_DEPTH), HTML entity
    unescaping, Unicode NFC normalisation, and header canonicalisation.
    """

    def normalize_request(
        self,
        path: str,
        body: str,
        headers: dict[str, str],
    ) -> NormalizedRequest:
        normalized_path, depth = self.normalize_path(path)
        normalized_body = self.normalize_body(body)
        normalized_headers = self.normalize_headers(headers)
        return NormalizedRequest(
            original_path=path,
            normalized_path=normalized_path,
            original_body=body,
            normalized_body=normalized_body,
            normalized_headers=normalized_headers,
            decode_depth=depth,
        )

    def normalize_path(self, path: str) -> tuple[str, int]:
        """Iteratively URL-decode and normalise a URL path.

        Returns:
            A tuple of (normalised_path, decode_depth_used).
        """
        decoded, depth = self._recursive_url_decode(path)
        decoded = self._normalize_unicode(decoded)
        decoded = self._normalize_whitespace(decoded)
        return decoded, depth

    def normalize_body(self, body: str) -> str:
        """URL-decode, HTML-unescape, and Unicode-normalise a request body."""
        if not body:
            return ""
        result, _ = self._recursive_url_decode(body)
        result = unescape(result)
        result = self._normalize_unicode(result)
        return result

    def normalize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Lowercase header names and strip surrounding whitespace from values."""
        return {k.lower().strip(): v.strip() for k, v in headers.items()}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _recursive_url_decode(self, value: str) -> tuple[str, int]:
        """Iteratively URL-decode up to MAX_DECODE_DEPTH times.

        Stops early when the output stabilises or a cycle is detected.

        Returns:
            A tuple of (decoded_string, actual_depth_used).
        """
        seen: set[str] = {value}
        current = value
        depth_used = 0
        for depth in range(1, MAX_DECODE_DEPTH + 1):
            decoded = unquote_plus(current)
            if decoded == current:
                # Already stable — no further decoding possible
                break
            if decoded in seen:
                # Cycle detected — stop to prevent infinite loops
                break
            seen.add(decoded)
            current = decoded
            depth_used = depth
        return current, depth_used

    def _normalize_unicode(self, value: str) -> str:
        """Apply Unicode NFC normalisation."""
        return unicodedata.normalize("NFC", value)

    def _normalize_whitespace(self, value: str) -> str:
        """Collapse consecutive whitespace to a single space and strip ends."""
        return re.sub(r"\s+", " ", value).strip()
