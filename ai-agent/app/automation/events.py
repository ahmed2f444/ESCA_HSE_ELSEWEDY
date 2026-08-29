"""Build deterministic automation events for an explicit delivery mode.

The functions in this module transform read-only detection results into
small event envelopes.  They do not write to MySQL and do not call an
external API.  The default is always side-effect-free ``dry_run``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Any


EVENT_SCHEMA_VERSION = "1.0"
DRY_RUN_MODE = "dry_run"
SPRING_MODE = "spring"
DATABASE_MODE = "database"
SUPPORTED_DELIVERY_MODES = frozenset({DRY_RUN_MODE, SPRING_MODE, DATABASE_MODE})

PERMIT_RULE_ID = "AUT-001"
CERTIFICATE_RULE_ID = "AUT-002"
CAPA_RULE_ID = "AUT-003"
RISK_RULE_ID = "AUT-004"


class AutomationEventError(ValueError):
    """Raised when a detection report cannot be converted safely."""


def _required_text(
    value: Any,
    *,
    field_name: str,
) -> str:
    text_value = str(value or "").strip()

    if not text_value:
        raise AutomationEventError(
            f"Missing required event field: {field_name}"
        )

    return text_value


def _json_value(value: Any) -> Any:
    """Convert common database scalar values to JSON-safe values."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            utc_value = value.replace(tzinfo=timezone.utc)
        else:
            utc_value = value.astimezone(timezone.utc)

        return utc_value.isoformat().replace("+00:00", "Z")

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    raise AutomationEventError(
        "Unsupported value type in event payload: "
        f"{type(value).__name__}"
    )


def _small_payload(
    candidate: Mapping[str, Any],
    fields: Sequence[str],
) -> dict[str, Any]:
    """Copy only approved, non-display fields into an event payload."""

    return {
        field: _json_value(candidate.get(field))
        for field in fields
        if candidate.get(field) is not None
    }


def _event_digest(
    *,
    rule_id: str,
    entity_type: str,
    entity_id: str,
    alert_code: str,
    occurrence_marker: str,
) -> str:
    """Create a stable digest without using names, emails, or descriptions."""

    canonical_value = json.dumps(
        {
            "alert_code": alert_code,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "occurrence_marker": occurrence_marker,
            "rule_id": rule_id,
            "schema_version": EVENT_SCHEMA_VERSION,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    return sha256(
        canonical_value.encode("utf-8")
    ).hexdigest()


def _build_event(
    *,
    rule_id: str,
    entity_type: str,
    entity_id: str,
    alert_code: str,
    action: str,
    occurrence_marker: str,
    evaluated_at_utc: str,
    business_date: str,
    payload: Mapping[str, Any],
    delivery_mode: str,
) -> dict[str, Any]:
    digest = _event_digest(
        rule_id=rule_id,
        entity_type=entity_type,
        entity_id=entity_id,
        alert_code=alert_code,
        occurrence_marker=occurrence_marker,
    )

    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": f"evt_{digest[:32]}",
        "idempotency_key": (
            f"hse-automation:v1:{digest}"
        ),
        "delivery_mode": delivery_mode,
        "rule_id": rule_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "alert_code": alert_code,
        "action": action,
        "evaluated_at_utc": evaluated_at_utc,
        "business_date": business_date,
        "payload": dict(payload),
    }


def _normalise_thresholds(values: Any) -> tuple[int, ...]:
    if not isinstance(values, Sequence) or isinstance(values, str):
        raise AutomationEventError(
            "CAPA escalation thresholds must be a list"
        )

    try:
        thresholds = tuple(
            sorted(
                {
                    int(value)
                    for value in values
                    if int(value) > 0
                }
            )
        )
    except (TypeError, ValueError) as exc:
        raise AutomationEventError(
            "CAPA escalation thresholds must contain integers"
        ) from exc

    return thresholds


def _capa_escalation_day(
    days_overdue: int,
    thresholds: tuple[int, ...],
) -> int | None:
    reached_thresholds = tuple(
        threshold
        for threshold in thresholds
        if threshold <= days_overdue
    )

    if not reached_thresholds:
        return None

    return max(reached_thresholds)


def _candidate_rows(
    candidates: Mapping[str, Any],
    group_name: str,
) -> Sequence[Mapping[str, Any]]:
    rows = candidates.get(group_name, [])

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise AutomationEventError(
            f"Candidate group must be a list: {group_name}"
        )

    for row in rows:
        if not isinstance(row, Mapping):
            raise AutomationEventError(
                f"Candidate row must be an object: {group_name}"
            )

    return rows


def build_automation_events(
    detection_report: Mapping[str, Any],
    *,
    delivery_mode: str = DRY_RUN_MODE,
) -> list[dict[str, Any]]:
    """Create deterministic events from a read-only detection report.

    Repeating this function with the same candidate state creates the same
    idempotency keys.  Display names, email aliases, free-text descriptions,
    titles, and hazards are deliberately excluded from event payloads.
    """

    if delivery_mode not in SUPPORTED_DELIVERY_MODES:
        raise AutomationEventError(
            "Unsupported automation delivery mode"
        )

    if detection_report.get("mode") != "read_only_detection":
        raise AutomationEventError(
            "Events require a read-only detection report"
        )

    evaluated_at_utc = _required_text(
        detection_report.get("evaluated_at_utc"),
        field_name="evaluated_at_utc",
    )
    business_date = _required_text(
        detection_report.get("business_date"),
        field_name="business_date",
    )

    raw_enabled_rules = detection_report.get("enabled_rule_ids", [])
    if not isinstance(raw_enabled_rules, Sequence) or isinstance(
        raw_enabled_rules,
        (str, bytes),
    ):
        raise AutomationEventError(
            "enabled_rule_ids must be a list"
        )

    enabled_rule_ids = {
        str(rule_id)
        for rule_id in raw_enabled_rules
    }

    candidates = detection_report.get("candidates")
    if not isinstance(candidates, Mapping):
        raise AutomationEventError(
            "Detection report candidates must be an object"
        )

    thresholds = detection_report.get("thresholds", {})
    if not isinstance(thresholds, Mapping):
        raise AutomationEventError(
            "Detection report thresholds must be an object"
        )

    events: list[dict[str, Any]] = []

    permit_rows = _candidate_rows(candidates, "permits")
    if permit_rows and PERMIT_RULE_ID not in enabled_rule_ids:
        raise AutomationEventError(
            "Permit candidates require AUT-001"
        )

    for candidate in permit_rows:
        entity_id = _required_text(
            candidate.get("permit_id"),
            field_name="permit_id",
        )
        alert_code = _required_text(
            candidate.get("alert_code"),
            field_name="alert_code",
        )
        expiry_at = _required_text(
            _json_value(candidate.get("expiry_at")),
            field_name="expiry_at",
        )

        events.append(
            _build_event(
                rule_id=PERMIT_RULE_ID,
                entity_type="PERMIT",
                entity_id=entity_id,
                alert_code=alert_code,
                action="FLAG_OVERDUE_PERMIT",
                occurrence_marker=expiry_at,
                evaluated_at_utc=evaluated_at_utc,
                business_date=business_date,
                payload=_small_payload(
                    candidate,
                    (
                        "permit_id",
                        "department_id",
                        "zone_id",
                        "requester_id",
                        "issuer_id",
                        "expiry_at",
                        "risk_level",
                        "status",
                        "minutes_overdue",
                    ),
                ),
                delivery_mode=delivery_mode,
            )
        )

    certificate_rows = _candidate_rows(
        candidates,
        "certificates",
    )
    if certificate_rows and CERTIFICATE_RULE_ID not in enabled_rule_ids:
        raise AutomationEventError(
            "Certificate candidates require AUT-002"
        )

    for candidate in certificate_rows:
        entity_id = _required_text(
            candidate.get("certificate_id"),
            field_name="certificate_id",
        )
        alert_code = _required_text(
            candidate.get("alert_code"),
            field_name="alert_code",
        )
        expiry_date = _required_text(
            _json_value(candidate.get("expiry_date")),
            field_name="expiry_date",
        )

        bracket = alert_code.lower().replace("certificate_", "")
        occurrence_marker = f"{expiry_date}|bracket={bracket}|date={business_date}"

        events.append(
            _build_event(
                rule_id=CERTIFICATE_RULE_ID,
                entity_type="CERTIFICATE",
                entity_id=entity_id,
                alert_code=alert_code,
                action="CREATE_TRAINING_REMINDER",
                occurrence_marker=occurrence_marker,
                evaluated_at_utc=evaluated_at_utc,
                business_date=business_date,
                payload=_small_payload(
                    candidate,
                    (
                        "certificate_id",
                        "employee_id",
                        "manager_id",
                        "course_id",
                        "expiry_date",
                        "status",
                        "days_to_expiry",
                    ),
                ),
                delivery_mode=delivery_mode,
            )
        )

    capa_thresholds = _normalise_thresholds(
        thresholds.get("capa_escalation_days", [])
    )
    capa_rows = _candidate_rows(candidates, "capa")
    if capa_rows and CAPA_RULE_ID not in enabled_rule_ids:
        raise AutomationEventError(
            "CAPA candidates require AUT-003"
        )

    for candidate in capa_rows:
        entity_id = _required_text(
            candidate.get("capa_id"),
            field_name="capa_id",
        )
        alert_code = _required_text(
            candidate.get("alert_code"),
            field_name="alert_code",
        )

        try:
            days_overdue = int(candidate.get("days_overdue"))
        except (TypeError, ValueError) as exc:
            raise AutomationEventError(
                "CAPA days_overdue must be an integer"
            ) from exc

        escalation_day = _capa_escalation_day(
            days_overdue,
            capa_thresholds,
        )

        if escalation_day is None:
            continue

        due_date = _required_text(
            _json_value(candidate.get("due_date")),
            field_name="due_date",
        )
        payload = _small_payload(
            candidate,
            (
                "capa_id",
                "incident_id",
                "finding_id",
                "assigned_to",
                "due_date",
                "priority",
                "status",
                "days_overdue",
            ),
        )
        payload["escalation_day"] = escalation_day

        events.append(
            _build_event(
                rule_id=CAPA_RULE_ID,
                entity_type="CAPA",
                entity_id=entity_id,
                alert_code=alert_code,
                action="CREATE_CAPA_ESCALATION",
                occurrence_marker=(
                    f"{due_date}|day={escalation_day}"
                ),
                evaluated_at_utc=evaluated_at_utc,
                business_date=business_date,
                payload=payload,
                delivery_mode=delivery_mode,
            )
        )

    risk_rows = _candidate_rows(candidates, "risks")
    if risk_rows and RISK_RULE_ID not in enabled_rule_ids:
        raise AutomationEventError(
            "Risk candidates require AUT-004"
        )

    risk_review_age_value = thresholds.get(
        "risk_review_age_days"
    )

    if risk_rows:
        try:
            risk_review_age_days = int(risk_review_age_value)
        except (TypeError, ValueError) as exc:
            raise AutomationEventError(
                "Risk review age must be an integer"
            ) from exc

        if risk_review_age_days < 0:
            raise AutomationEventError(
                "Risk review age cannot be negative"
            )
    else:
        risk_review_age_days = None

    for candidate in risk_rows:
        entity_id = _required_text(
            candidate.get("risk_id"),
            field_name="risk_id",
        )
        alert_code = _required_text(
            candidate.get("alert_code"),
            field_name="alert_code",
        )
        last_reviewed_at = _json_value(
            candidate.get("last_reviewed_at")
        )
        next_review_date = _json_value(
            candidate.get("next_review_date")
        )
        occurrence_marker = json.dumps(
            {
                "last_reviewed_at": (
                    last_reviewed_at or "never-reviewed"
                ),
                "next_review_date": next_review_date,
                "review_age_days": risk_review_age_days,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )

        events.append(
            _build_event(
                rule_id=RISK_RULE_ID,
                entity_type="RISK",
                entity_id=entity_id,
                alert_code=alert_code,
                action="FLAG_RISK_FOR_REVIEW",
                occurrence_marker=occurrence_marker,
                evaluated_at_utc=evaluated_at_utc,
                business_date=business_date,
                payload=_small_payload(
                    candidate,
                    (
                        "risk_id",
                        "department_id",
                        "zone_id",
                        "owner_id",
                        "inherent_score",
                        "risk_level",
                        "residual_score",
                        "status",
                        "last_reviewed_at",
                        "next_review_date",
                        "days_since_review",
                    ),
                ),
                delivery_mode=delivery_mode,
            )
        )

    events.sort(
        key=lambda event: (
            event["rule_id"],
            event["entity_id"],
            event["alert_code"],
            event["event_id"],
        )
    )

    return events
