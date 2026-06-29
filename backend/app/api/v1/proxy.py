import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.repositories.detection_result_repo import DetectionResultRepository
from app.repositories.processed_log_repo import ProcessedLogRepository
from app.repositories.raw_log_repo import RawLogRepository
from app.repositories.replay_repo import ReplayRepository
from app.repositories.rule_stat_repo import RuleStatRepository
from app.rules.engine import RuleEngine
from app.services.cache_service import CacheService
from app.services.detection_service import DetectionService
from app.services.proxy_service import ProxyService
from app.utils.helpers import get_client_ip, sanitize_null_bytes

logger = get_logger(__name__)

router = APIRouter(tags=["proxy"])

_ATTACK_TYPE_TO_COUNTER: dict[str, str] = {
    "SQLI": "attack_sqli",
    "XSS": "attack_xss",
    "PATH_TRAVERSAL": "attack_path_traversal",
    "COMMAND_INJECTION": "attack_command_injection",
}


@router.api_route(
    "/{target}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    summary="Inline WAF Proxy",
    description="Intercepts, inspects, logs, and forwards requests to target applications.",
)
async def proxy_request(
    target: str,
    path: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
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

    # ── Resolve Request Properties ────────────────────────────────────────
    ip_address = get_client_ip(request)
    method = request.method
    full_path = f"/{target}/{path}"
    if request.url.query:
        full_path += f"?{request.url.query}"
    
    headers = dict(request.headers)
    body_bytes = await request.body()
    try:
        body_str = body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        body_str = body_bytes.decode("latin-1", errors="replace")

    request_size = len(body_bytes)

    # ── Step 1: Persist raw request ───────────────────────────────────────
    raw_log = await raw_repo.create(
        ip_address=ip_address,
        method=method,
        path=sanitize_null_bytes(full_path),
        headers=sanitize_null_bytes(headers),
        body=sanitize_null_bytes(body_str) or None,
        user_agent=sanitize_null_bytes(headers.get("user-agent", headers.get("User-Agent"))),
        request_size=request_size,
    )

    # ── Step 2: Run detection pipeline ───────────────────────────────────
    detection_output = detection_svc.detect(
        path=full_path,
        body=body_str,
        headers=headers,
        ip_address=ip_address,
        method=method,
    )

    latency_ms = (time.perf_counter() - start_time) * 1000
    decision = "blocked" if not detection_output.allowed else "allowed"

    # ── Step 3: Persist processed log ────────────────────────────────────
    await processed_repo.create(
        raw_log_id=raw_log.id,
        normalized_path=sanitize_null_bytes(detection_output.normalized_path),
        normalized_body=sanitize_null_bytes(detection_output.normalized_body),
        fingerprint=detection_output.fingerprint,
        decision=decision,
        attack_type=detection_output.attack_type,
        rule_version=rule_engine.ruleset_version,
        response_status=403 if not detection_output.allowed else 0,
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
        matched_pattern=sanitize_null_bytes(detection_output.matched_pattern),
        metadata=sanitize_null_bytes(detection_output.detection_metadata),
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

        if detection_output.rule_id and detection_output.attack_type:
            await rule_stat_repo.increment(
                rule_id=detection_output.rule_id,
                rule_name=detection_output.matched_rule or detection_output.rule_id,
                category=detection_output.attack_type,
                severity=detection_output.severity or "MEDIUM",
            )

        await replay_repo.enqueue(
            request_log_id=str(raw_log.id),
            payload=sanitize_null_bytes(body_str),
            headers=sanitize_null_bytes(headers),
            method=method,
            path=sanitize_null_bytes(full_path),
        )

        await db.commit()

        logger.warning(
            "waf.blocked",
            ip=ip_address,
            path=full_path,
            attack_type=detection_output.attack_type,
            rule_id=detection_output.rule_id,
            severity=detection_output.severity,
            latency_ms=round(latency_ms, 2),
        )

        return Response(
            content='{"error": "Forbidden", "message": "Request blocked by WAF"}',
            status_code=403,
            media_type="application/json"
        )

    # ── Allowed path: forward to upstream ────────────────────────────────
    await cache_svc.incr_counter("allowed_total")

    upstream_response = await proxy.forward_request(
        target=target,
        path=f"/{path}",
        method=method,
        headers=headers,
        body=body_bytes,
        query_string=request.url.query.encode('utf-8') if request.url.query else b"",
    )

    # Update processed log with actual response status
    await db.execute(
        text("UPDATE processed_request_logs SET response_status = :status WHERE raw_log_id = :id"),
        {"status": upstream_response.status_code, "id": raw_log.id}
    )
    
    await db.commit()

    logger.info(
        "waf.allowed",
        ip=ip_address,
        path=full_path,
        upstream_status=upstream_response.status_code,
        latency_ms=round(latency_ms, 2),
    )

    # Strip hop-by-hop and encoding headers from upstream response
    resp_headers = {}
    for k, v in upstream_response.headers.items():
        if k.lower() not in ("content-encoding", "content-length", "transfer-encoding", "connection"):
            resp_headers[k] = v

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=resp_headers,
    )
