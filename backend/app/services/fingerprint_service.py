import hashlib


def generate_fingerprint(normalized_path: str, normalized_body: str) -> str:
    """Generate a SHA-256 fingerprint from the normalised path and body.

    Used for deduplication, replay attack detection, and training dataset
    generation.  The fingerprint is stable across requests with identical
    normalised content regardless of encoding variations.

    Args:
        normalized_path: URL-decoded, Unicode-normalised request path.
        normalized_body: URL-decoded, HTML-unescaped, normalised request body.

    Returns:
        Lowercase hex-encoded SHA-256 digest (64 characters).
    """
    content = normalized_path + normalized_body
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
