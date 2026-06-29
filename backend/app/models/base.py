"""Import all ORM models so Alembic's autogenerate can discover them."""

from app.models.detection_result import DetectionResultModel  # noqa: F401
from app.models.processed_request_log import ProcessedRequestLog  # noqa: F401
from app.models.raw_request_log import RawRequestLog  # noqa: F401
from app.models.request_replay import RequestReplay  # noqa: F401
from app.models.rule_stat import RuleStat  # noqa: F401

__all__ = [
    "RawRequestLog",
    "ProcessedRequestLog",
    "DetectionResultModel",
    "RequestReplay",
    "RuleStat",
]
