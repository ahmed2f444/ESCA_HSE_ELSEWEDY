"""Create a safe, aggregate-only automation preview.

This is the application layer for a future authenticated Admin Preview API
and for a local preview CLI. It deliberately returns counts only: raw
detection candidates, event payloads, entity identifiers, idempotency keys,
names, e-mail addresses, and free text never leave this module.

The module performs no writes and has no HTTP/network dependency. It verifies
the current MySQL session is the configured read-only account, runs detection,
rolls the transaction back, and closes the session before events are planned.
Do not mount an HTTP route until the team provides a real Admin-auth dependency.
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import datetime
from typing import Any, NoReturn

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.automation.events import build_automation_events
from app.automation.service import SUPPORTED_RULE_IDS, run_detection
from app.config import get_settings
from app.database import SessionLocal, WRITE_PRIVILEGES


logger = logging.getLogger(__name__)

DETECTION_COUNT_FIELDS = (
    "overdue_permits",
    "certificate_alerts",
    "overdue_capa",
    "stale_high_risks",
)


class AutomationPreviewError(RuntimeError):
    """Raised when a preview cannot be generated safely."""


def _fail(*, stage: str, error: Exception) -> NoReturn:
    """Log only a safe stage and exception type, never its message."""

    logger.error(
        "automation_preview_failed stage=%s error_type=%s",
        stage,
        type(error).__name__,
    )
    raise AutomationPreviewError(
        f"Automation preview failed during {stage}"
    ) from None


def _required_text(value: Any, *, field_name: str) -> str:
    text_value = str(value or "").strip()
    if not text_value:
        raise ValueError(f"Missing preview field: {field_name}")
    return text_value


def _normalise_rule_ids(
    rule_ids: Collection[str] | None,
) -> tuple[str, ...] | None:
    if rule_ids is None:
        return None
    if isinstance(rule_ids, (str, bytes)):
        raise ValueError("rule_ids must be a collection, not a string")

    normalised = tuple(
        sorted({str(rule_id).strip() for rule_id in rule_ids})
    )
    if not normalised or any(not rule_id for rule_id in normalised):
        raise ValueError("rule_ids cannot be empty")

    unsupported = set(normalised) - SUPPORTED_RULE_IDS
    if unsupported:
        raise ValueError("rule_ids contains an unsupported rule")
    return normalised


def _validate_as_of(as_of: datetime | None) -> None:
    if as_of is not None and (
        as_of.tzinfo is None or as_of.utcoffset() is None
    ):
        raise ValueError("as_of must include timezone information")


def verify_read_only_session(session: Session) -> Mapping[str, str]:
    """Fail closed unless this is the configured read-only MySQL account."""

    settings = get_settings()
    identity = session.execute(
        text(
            """
            SELECT
                DATABASE() AS database_name,
                CURRENT_USER() AS database_user
            """
        )
    ).mappings().one()
    grants = session.execute(
        text("SHOW GRANTS FOR CURRENT_USER()")
    ).scalars().all()

    database_name = str(identity["database_name"])
    database_user = str(identity["database_user"])
    configured_user = str(settings.db_user)
    actual_user = database_user.split("@", 1)[0]
    normalised_grants = " ".join(str(grant).upper() for grant in grants)
    has_write_privilege = any(
        privilege in normalised_grants
        for privilege in WRITE_PRIVILEGES
    )

    if database_name != settings.db_name:
        raise PermissionError("Unexpected preview database")
    if actual_user != configured_user:
        raise PermissionError("Unexpected preview database account")
    if has_write_privilege:
        raise PermissionError("Preview database account is not read-only")

    return {
        "database_name": database_name,
        "database_user": database_user,
        "read_only": "on",
    }


def _safe_detection_summary(report: Mapping[str, Any]) -> dict[str, int]:
    raw_summary = report.get("summary")
    if not isinstance(raw_summary, Mapping):
        raise ValueError("Detection summary must be an object")

    result: dict[str, int] = {}
    for field_name in DETECTION_COUNT_FIELDS:
        raw_value = raw_summary.get(field_name)
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise ValueError("Detection counts must be integers")
        if raw_value < 0:
            raise ValueError("Detection counts cannot be negative")
        result[field_name] = raw_value

    total_candidates = raw_summary.get("total_candidates")
    if (
        isinstance(total_candidates, bool)
        or not isinstance(total_candidates, int)
        or total_candidates < 0
        or total_candidates != sum(result.values())
    ):
        raise ValueError("Detection total is inconsistent")

    result["total_candidates"] = total_candidates
    return result


def _safe_enabled_rules(report: Mapping[str, Any]) -> list[str]:
    raw_rules = report.get("enabled_rule_ids")
    if not isinstance(raw_rules, Sequence) or isinstance(
        raw_rules, (str, bytes)
    ):
        raise ValueError("enabled_rule_ids must be a list")

    rule_ids = sorted({str(rule_id) for rule_id in raw_rules})
    if set(rule_ids) - SUPPORTED_RULE_IDS:
        raise ValueError("Detection enabled an unsupported rule")
    return rule_ids


def _safe_event_summary(
    events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise ValueError("Event batch must be a list")

    by_rule: Counter[str] = Counter()
    by_alert_code: Counter[str] = Counter()
    by_action: Counter[str] = Counter()

    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("Every event must be an object")
        if event.get("delivery_mode") != "dry_run":
            raise ValueError("Preview events must be dry-run")

        by_rule[
            _required_text(event.get("rule_id"), field_name="rule_id")
        ] += 1
        by_alert_code[
            _required_text(event.get("alert_code"), field_name="alert_code")
        ] += 1
        by_action[
            _required_text(event.get("action"), field_name="action")
        ] += 1

    return {
        "total_events": len(events),
        "events_by_rule": dict(sorted(by_rule.items())),
        "events_by_alert_code": dict(sorted(by_alert_code.items())),
        "events_by_action": dict(sorted(by_action.items())),
        "delivered_events": 0,
    }


def build_automation_preview(
    *,
    as_of: datetime | None = None,
    rule_ids: Collection[str] | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
    safety_checker: Callable[[Session], Mapping[str, str]] = (
        verify_read_only_session
    ),
    detector: Callable[..., Mapping[str, Any]] = run_detection,
    event_builder: Callable[
        [Mapping[str, Any]], Sequence[Mapping[str, Any]]
    ] = build_automation_events,
) -> dict[str, Any]:
    """Return aggregate preview counts with no PII and no side effects."""

    try:
        _validate_as_of(as_of)
        selected_rule_ids = _normalise_rule_ids(rule_ids)
    except Exception as exc:
        _fail(stage="request_validation", error=exc)

    # The only stage permitted to hold a database session.
    try:
        with session_factory() as session:
            try:
                safety = safety_checker(session)
                if safety.get("read_only") != "on":
                    raise PermissionError("Preview session is not read-only")
                detection_report = detector(
                    session=session,
                    as_of=as_of,
                    rule_ids=selected_rule_ids,
                )
            finally:
                session.rollback()
    except Exception as exc:
        _fail(stage="detection", error=exc)

    # The context above has exited: planning holds no DB connection.
    try:
        if detection_report.get("mode") != "read_only_detection":
            raise ValueError("Preview requires read-only detection")
        detection_summary = _safe_detection_summary(detection_report)
        enabled_rule_ids = _safe_enabled_rules(detection_report)
        events = event_builder(detection_report)
        event_summary = _safe_event_summary(events)
        evaluated_at_utc = _required_text(
            detection_report.get("evaluated_at_utc"),
            field_name="evaluated_at_utc",
        )
        business_timezone = _required_text(
            detection_report.get("business_timezone"),
            field_name="business_timezone",
        )
        business_date = _required_text(
            detection_report.get("business_date"),
            field_name="business_date",
        )
    except Exception as exc:
        _fail(stage="event_planning", error=exc)

    logger.info(
        "automation_preview_completed candidates=%d events=%d rules=%d "
        "mode=dry_run_preview",
        detection_summary["total_candidates"],
        event_summary["total_events"],
        len(enabled_rule_ids),
    )

    # Explicit projection only. Never copy report candidates or event data.
    return {
        "status": "completed",
        "mode": "dry_run_preview",
        "read_only": True,
        "evaluated_at_utc": evaluated_at_utc,
        "business_timezone": business_timezone,
        "business_date": business_date,
        "enabled_rule_ids": enabled_rule_ids,
        "detection_summary": detection_summary,
        "event_summary": event_summary,
    }
