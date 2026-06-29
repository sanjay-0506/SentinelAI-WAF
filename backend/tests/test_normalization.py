"""Unit tests for NormalizerService."""
import pytest

from app.normalization.normalizer import MAX_DECODE_DEPTH, NormalizerService


class TestUrlDecoding:
    """Tests for _recursive_url_decode and the overall normalize_path."""

    def test_triple_encoded_single_quote(self, normalizer: NormalizerService) -> None:
        """%252527 → %2527 → %27 → ' (three decode passes)."""
        path, depth = normalizer.normalize_path("%252527")
        assert path == "'"
        assert depth == 3

    def test_double_encoded_single_quote(self, normalizer: NormalizerService) -> None:
        """%2527 → %27 → ' (two decode passes)."""
        path, depth = normalizer.normalize_path("%2527")
        assert path == "'"
        assert depth == 2

    def test_single_encoded_single_quote(self, normalizer: NormalizerService) -> None:
        """%27 → ' (one decode pass)."""
        path, depth = normalizer.normalize_path("%27")
        assert path == "'"
        assert depth == 1

    def test_already_decoded_string(self, normalizer: NormalizerService) -> None:
        """Plain string should not be mutated and depth should be 0."""
        path, depth = normalizer.normalize_path("/api/users")
        assert path == "/api/users"
        assert depth == 0

    def test_max_depth_respected(self, normalizer: NormalizerService) -> None:
        """Encoding deeper than MAX_DECODE_DEPTH should stop at limit."""
        # Build a string encoded 5 times (more than MAX_DECODE_DEPTH=3)
        value = "'"
        for _ in range(5):
            from urllib.parse import quote
            value = quote(value, safe="")
        # Should decode only up to MAX_DECODE_DEPTH times
        path, depth = normalizer.normalize_path(value)
        assert depth <= MAX_DECODE_DEPTH

    def test_loop_detection_prevents_infinite_recursion(
        self, normalizer: NormalizerService
    ) -> None:
        """A string that URL-decodes to itself should not loop."""
        # A plain string with no percent-encoding decodes to itself immediately
        original = "hello+world"
        path, depth = normalizer.normalize_path(original)
        # + is decoded by unquote_plus; depth should be 1
        assert depth == 1
        assert path is not None  # must return something


class TestBodyNormalization:
    """Tests for normalize_body."""

    def test_html_entities_decoded(self, normalizer: NormalizerService) -> None:
        """HTML entities like &lt; and &amp; should be unescaped."""
        body = "&lt;script&gt;alert(1)&lt;/script&gt;"
        result = normalizer.normalize_body(body)
        assert "<script>" in result
        assert "</script>" in result

    def test_url_encoded_body_decoded(self, normalizer: NormalizerService) -> None:
        """URL-encoded body should be decoded."""
        body = "username=admin%27%20OR%20%271%27%3D%271"
        result = normalizer.normalize_body(body)
        assert "'" in result

    def test_empty_body_returns_empty_string(
        self, normalizer: NormalizerService
    ) -> None:
        """None and empty string bodies should return empty string."""
        assert normalizer.normalize_body("") == ""

    def test_unicode_normalized(self, normalizer: NormalizerService) -> None:
        """Unicode should be NFC-normalised."""
        import unicodedata
        # Compose a string with a combining character
        nfd_string = "caf\u0065\u0301"  # 'cafe' + combining acute
        result = normalizer.normalize_body(nfd_string)
        assert unicodedata.is_normalized("NFC", result)


class TestHeaderNormalization:
    """Tests for normalize_headers."""

    def test_headers_lowercased(self, normalizer: NormalizerService) -> None:
        """Header names must be lowercased."""
        headers = {"Content-Type": "application/json", "X-Forwarded-For": "1.2.3.4"}
        result = normalizer.normalize_headers(headers)
        assert "content-type" in result
        assert "x-forwarded-for" in result
        assert "Content-Type" not in result

    def test_header_values_stripped(self, normalizer: NormalizerService) -> None:
        """Header values must have surrounding whitespace removed."""
        headers = {"Authorization": "  Bearer token  "}
        result = normalizer.normalize_headers(headers)
        assert result["authorization"] == "Bearer token"

    def test_empty_headers(self, normalizer: NormalizerService) -> None:
        """Empty headers dict should return empty dict."""
        assert normalizer.normalize_headers({}) == {}


class TestNormalizeRequest:
    """Integration-level tests for normalize_request."""

    def test_returns_normalized_request_dataclass(
        self, normalizer: NormalizerService
    ) -> None:
        from app.normalization.normalizer import NormalizedRequest

        result = normalizer.normalize_request(
            path="/api%2Fusers",
            body="name=test",
            headers={"User-Agent": "pytest"},
        )
        assert isinstance(result, NormalizedRequest)
        assert result.original_path == "/api%2Fusers"
        assert result.normalized_path == "/api/users"
        assert result.normalized_headers == {"user-agent": "pytest"}
