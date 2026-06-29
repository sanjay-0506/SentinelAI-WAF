import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.repositories.detection_result_repo import DetectionResultRepository
from app.repositories.processed_log_repo import ProcessedLogRepository
from app.repositories.raw_log_repo import RawLogRepository
from app.repositories.replay_repo import ReplayRepository
from app.repositories.rule_stat_repo import RuleStatRepository
from app.rules.engine import RuleEngine
from app.schemas.inspect import InspectRequest, InspectResponse
from app.services.cache_service import CacheService
from app.services.detection_service import DetectionService
from app.services.proxy_service import ProxyService
from app.utils.helpers import get_client_ip

logger = get_logger(__name__)

router = APIRouter(prefix="/inspect", tags=["inspect"])

_ATTACK_TYPE_TO_COUNTER: dict[str, str] = {
    "SQLI": "attack_sqli",
    "XSS": "attack_xss",
    "PATH_TRAVERSAL": "attack_path_traversal",
    "COMMAND_INJECTION": "attack_command_injection",
}


@router.post(
    "",
    response_model=InspectResponse,
    summary="Inspect a request against WAF rules",
    description=(
        "Submit an HTTP request for WAF evaluation. "
        "Blocked requests are logged and queued for replay. "
        "Allowed requests are forwarded to the upstream target."
    ),
)
async def inspect(
    payload: InspectRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InspectResponse:
    start_time = time.perf_counter()

    # ── Resolve dependencies ──────────────────────────────────────────────
    rule_engine: RuleEngine = request.app.state.rule_engine
    proxy: ProxyService = request.app.state.proxy_service
    normalizer = request.app.state.normalizer

    detection_svc = DetectionService(normalizer=normalizer, rule_engine=rule_engine)
    cache_svc = CacheService()
    raw_repo = RawLogRepository(db)
    processed_repo = ProcessedLogRepository(db)
    detection_repo = DetectionResultRepository(db)
    replay_repo = ReplayRepository(db)
    rule_stat_repo = RuleStatRepository(db)

    # ── Resolve client IP ─────────────────────────────────────────────────
    ip_address = payload.ip_address or get_client_ip(request)

    # ── Step 1: Persist raw request ───────────────────────────────────────
    raw_log = await raw_repo.create(
        ip_address=ip_address,
        method=payload.method,
        path=payload.path,
        headers=payload.headers,
        body=payload.body or None,
        user_agent=payload.headers.get("user-agent", payload.headers.get("User-Agent")),
        request_size=len((payload.body or "").encode("utf-8")),
    )

    # ── Step 2: Run detection pipeline ───────────────────────────────────
    detection_output = detection_svc.detect(
        path=payload.path,
        body=payload.body,
        headers=payload.headers,
        ip_address=ip_address,
        method=payload.method,
    )

    latency_ms = (time.perf_counter() - start_time) * 1000
    decision = "blocked" if not detection_output.allowed else "allowed"

    # ── Step 3: Persist processed log ────────────────────────────────────
    await processed_repo.create(
        raw_log_id=raw_log.id,
        normalized_path=detection_output.normalized_path,
        normalized_body=detection_output.normalized_body,
        fingerprint=detection_output.fingerprint,
        decision=decision,
        attack_type=detection_output.attack_type,
        rule_version=rule_engine.ruleset_version,
        response_status=403 if not detection_output.allowed else 200,
        latency_ms=latency_ms,
    )

    # ── Step 4: Persist detection result ─────────────────────────────────
    await detection_repo.create(
        request_id=raw_log.id,
        engine="rule_engine",
        rule_id=detection_output.rule_id,
        severity=detection_output.severity,
        confidence=detection_output.confidence,
        decision=decision,
        matched_pattern=detection_output.matched_pattern,
        metadata=detection_output.detection_metadata,
    )

    # ── Step 5: Update counters and rule stats ────────────────────────────
    await cache_svc.incr_counter("requests_total")
    await cache_svc.record_latency(latency_ms)

    if not detection_output.allowed:
        await cache_svc.incr_counter("blocked_total")
        if detection_output.attack_type:
            counter_key = _ATTACK_TYPE_TO_COUNTER.get(
                detection_output.attack_type, f"attack_{detection_output.attack_type.lower()}"
            )
            await cache_svc.incr_counter(counter_key)

        # Persist rule hit stat
        if detection_output.rule_id and detection_output.attack_type:
            await rule_stat_repo.increment(
                rule_id=detection_output.rule_id,
                rule_name=detection_output.matched_rule or detection_output.rule_id,
                category=detection_output.attack_type,
                severity=detection_output.severity or "MEDIUM",
            )

        # Enqueue for Level-2 replay
        await replay_repo.enqueue(
            request_log_id=str(raw_log.id),
            payload=payload.body,
            headers=payload.headers,
            method=payload.method,
            path=payload.path,
        )

        await db.commit()

        logger.warning(
            "waf.blocked",
            ip=ip_address,
            path=payload.path,
            attack_type=detection_output.attack_type,
            rule_id=detection_output.rule_id,
            severity=detection_output.severity,
            latency_ms=round(latency_ms, 2),
        )

        return InspectResponse(
            allowed=False,
            attack_type=detection_output.attack_type,
            confidence=detection_output.confidence,
            matched_rule=detection_output.matched_rule,
            rule_id=detection_output.rule_id,
            severity=detection_output.severity,
            fingerprint=detection_output.fingerprint,
            request_id=str(raw_log.id),
            latency_ms=round(latency_ms, 2),
        )

    # ── Allowed path: forward to upstream ────────────────────────────────
    await cache_svc.incr_counter("allowed_total")

    # Forward request asynchronously
    body_bytes = (payload.body or "").encode("utf-8")
    
    # Extract target from path (e.g. /juice-shop/...)
    target = ""
    upstream_path = payload.path
    if payload.path.startswith("/juice-shop"):
        target = "juice-shop"
        upstream_path = payload.path.removeprefix("/juice-shop") or "/"
    elif payload.path.startswith("/dvwa"):
        target = "dvwa"
        upstream_path = payload.path.removeprefix("/dvwa") or "/"
        
    upstream_response = await proxy.forward_request(
        target=target,
        path=upstream_path,
        method=payload.method,
        headers=payload.headers,
        body=body_bytes,
    )

    await db.commit()

    logger.info(
        "waf.allowed",
        ip=ip_address,
        path=payload.path,
        upstream_status=upstream_response.status_code,

        latency_ms=round(latency_ms, 2),
    )

    return InspectResponse(
        allowed=True,
        attack_type=None,
        confidence=detection_output.confidence,
        matched_rule=None,
        rule_id=None,
        severity=None,
        fingerprint=detection_output.fingerprint,
        request_id=str(raw_log.id),
        latency_ms=round(latency_ms, 2),
    )
