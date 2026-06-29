from dataclasses import dataclass, field

from app.normalization.normalizer import NormalizerService
from app.rules.engine import DetectionResult, RuleEngine
from app.services.fingerprint_service import generate_fingerprint


@dataclass
class DetectionOutput:
    """Fully-resolved output from the detection pipeline.

    Contains all fields required to persist both the raw and processed log
    records as well as the detection result record.
    """

    # Normalisation outputs
    original_path: str
    normalized_path: str
    original_body: str
    normalized_body: str
    normalized_headers: dict[str, str]
    decode_depth: int

    # Detection outputs
    allowed: bool
    attack_type: str | None
    confidence: float
    matched_rule: str | None
    rule_id: str | None
    severity: str | None
    matched_pattern: str | None
    detection_metadata: dict = field(default_factory=dict)

    # Request metadata
    fingerprint: str = ""
    ip_address: str = "127.0.0.1"
    method: str = "GET"
    user_agent: str = ""
    request_size: int = 0


class DetectionService:
    """Orchestrates the Level-1 WAF detection pipeline.

    Pipeline steps:
    1. Normalise the raw request (path, body, headers).
    2. Evaluate the normalised request against the rule engine.
    3. Generate a content fingerprint for deduplication.
    4. Return a structured :class:`DetectionOutput`.
    """

    def __init__(
        self,
        normalizer: NormalizerService,
        rule_engine: RuleEngine,
    ) -> None:
        self._normalizer = normalizer
        self._rule_engine = rule_engine

    def detect(
        self,
        path: str,
        body: str,
        headers: dict[str, str],
        ip_address: str = "127.0.0.1",
        method: str = "GET",
    ) -> DetectionOutput:
        """Run the full detection pipeline and return a :class:`DetectionOutput`.

        Args:
            path: Raw request URL path.
            body: Raw request body as a string.
            headers: Raw HTTP headers as a dict.
            ip_address: Client IP address.
            method: HTTP method (GET, POST, …).

        Returns:
            A :class:`DetectionOutput` populated with normalisation and
            detection results.
        """
        # Step 1 — normalise
        normalised = self._normalizer.normalize_request(path, body, headers)

        # Step 2 — evaluate against rules
        result: DetectionResult = self._rule_engine.evaluate(
            normalised.normalized_path,
            normalised.normalized_body,
            normalised.normalized_headers,
        )

        # Step 3 — fingerprint
        fingerprint = generate_fingerprint(
            normalised.normalized_path,
            normalised.normalized_body,
        )

        # Step 4 — collate user_agent and request_size
        user_agent = headers.get("user-agent", headers.get("User-Agent", ""))
        request_size = len(body.encode("utf-8")) if body else 0

        return DetectionOutput(
            original_path=normalised.original_path,
            normalized_path=normalised.normalized_path,
            original_body=normalised.original_body,
            normalized_body=normalised.normalized_body,
            normalized_headers=normalised.normalized_headers,
            decode_depth=normalised.decode_depth,
            allowed=result.allowed,
            attack_type=result.attack_type,
            confidence=result.confidence,
            matched_rule=result.matched_rule,
            rule_id=result.rule_id,
            severity=result.severity,
            matched_pattern=result.matched_pattern,
            detection_metadata=result.metadata,
            fingerprint=fingerprint,
            ip_address=ip_address,
            method=method,
            user_agent=user_agent,
            request_size=request_size,
        )
