from collections.abc import Collection, Mapping
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.automation.repository import (
    find_certificate_alerts,
    find_overdue_capa,
    find_overdue_permits,
    find_stale_high_risks,
    get_active_automation_rules,
)
from app.config import get_settings


PERMIT_RULE_ID = "AUT-001"
CERTIFICATE_RULE_ID = "AUT-002"
CAPA_RULE_ID = "AUT-003"
RISK_RULE_ID = "AUT-004"

SUPPORTED_RULE_IDS = frozenset(
    {
        PERMIT_RULE_ID,
        CERTIFICATE_RULE_ID,
        CAPA_RULE_ID,
        RISK_RULE_ID,
    }
)

EXPECTED_ENTITY_TYPES = {
    PERMIT_RULE_ID: "PERMIT",
    CERTIFICATE_RULE_ID: "CERTIFICATE",
    CAPA_RULE_ID: "CAPA",
    RISK_RULE_ID: "RISK",
}

# Prevent accidental values large enough to overflow date arithmetic or
# turn a configuration typo into an effectively unbounded alert window.
MAX_THRESHOLD_DAYS = 3650


class AutomationConfigurationError(ValueError):
    """
    Raised when an active automation rule
    has invalid configuration.
    """


def _get_rule(
    rules: dict[str, dict[str, Any]],
    rule_id: str,
    expected_entity_type: str,
) -> dict[str, Any] | None:
    rule = rules.get(rule_id)

    if rule is None:
        return None

    if rule["entity_type"] != expected_entity_type:
        raise AutomationConfigurationError(
            f"{rule_id} must use "
            f"entity_type={expected_entity_type}"
        )

    return rule


def _select_requested_rules(
    rules: dict[str, dict[str, Any]],
    rule_ids: Collection[str] | None,
) -> dict[str, dict[str, Any]]:
    if rule_ids is None:
        return rules

    if isinstance(rule_ids, str):
        requested_rule_ids = {rule_ids}
    else:
        requested_rule_ids = {
            str(rule_id)
            for rule_id in rule_ids
        }

    unsupported_rule_ids = (
        requested_rule_ids
        - SUPPORTED_RULE_IDS
    )

    if unsupported_rule_ids:
        unsupported_text = ", ".join(
            sorted(unsupported_rule_ids)
        )

        raise AutomationConfigurationError(
            "Unsupported automation rule IDs: "
            f"{unsupported_text}"
        )

    return {
        rule_id: rule
        for rule_id, rule in rules.items()
        if rule_id in requested_rule_ids
    }


def _parse_non_negative_integers(
    rule: Mapping[str, Any],
) -> tuple[int, ...]:
    rule_id = str(rule.get("rule_id") or "").strip()
    raw_threshold = rule.get("threshold_value")
    
    if isinstance(raw_threshold, (list, tuple, set)):
        try:
            values = tuple(int(v) for v in raw_threshold)
        except (ValueError, TypeError) as exc:
            raise AutomationConfigurationError(
                f"{rule_id} threshold_value must contain integers"
            ) from exc
    else:
        raw_value = "" if raw_threshold is None else str(raw_threshold)
        try:
            values = tuple(
                int(piece.strip())
                for piece in raw_value.split(",")
                if piece.strip()
            )
        except ValueError as exc:
            raise AutomationConfigurationError(
                f"{rule_id} threshold_value "
                "must contain integers"
            ) from exc

    if not values:
        raise AutomationConfigurationError(
            f"{rule_id} threshold_value "
            "cannot be empty"
        )

    if any(value < 0 for value in values):
        raise AutomationConfigurationError(
            f"{rule_id} thresholds "
            "cannot be negative"
        )

    if any(value > MAX_THRESHOLD_DAYS for value in values):
        raise AutomationConfigurationError(
            f"{rule_id} thresholds cannot exceed "
            f"{MAX_THRESHOLD_DAYS} days"
        )

    return tuple(
        sorted(
            set(values),
            reverse=True,
        )
    )


def _parse_single_non_negative_integer(
    rule: Mapping[str, Any],
) -> int:
    values = _parse_non_negative_integers(rule)

    if len(values) != 1:
        raise AutomationConfigurationError(
            f"{str(rule.get('rule_id') or '').strip()} must contain "
            "exactly one threshold"
        )

    return values[0]


def validate_rule_configuration(
    rule: Mapping[str, Any],
) -> None:
    """Validate one active rule before it can be scheduled or executed.

    This is intentionally shared by the scheduler and detector so startup
    validation cannot drift away from the rules used during execution.
    """

    raw_rule_id = rule.get("rule_id")

    if not isinstance(raw_rule_id, str):
        raise AutomationConfigurationError(
            "Automation rule_id must be exact text"
        )

    rule_id = raw_rule_id.strip()

    if raw_rule_id != rule_id:
        raise AutomationConfigurationError(
            "Automation rule_id cannot contain surrounding whitespace"
        )

    if rule_id not in SUPPORTED_RULE_IDS:
        raise AutomationConfigurationError(
            "Unsupported automation rule configuration"
        )

    entity_type = rule.get("entity_type")
    expected_entity_type = EXPECTED_ENTITY_TYPES[rule_id]

    if not isinstance(entity_type, str) or entity_type != expected_entity_type:
        raise AutomationConfigurationError(
            f"{rule_id} must use "
            f"entity_type={expected_entity_type}"
        )

    if rule_id == PERMIT_RULE_ID:
        threshold = _parse_single_non_negative_integer(rule)
        if threshold < 0:
            raise AutomationConfigurationError(
                f"{PERMIT_RULE_ID} requires a non-negative threshold"
            )
    elif rule_id == CERTIFICATE_RULE_ID:
        _parse_non_negative_integers(rule)
    elif rule_id == CAPA_RULE_ID:
        thresholds = _parse_non_negative_integers(rule)
        if any(threshold < 0 for threshold in thresholds):
            raise AutomationConfigurationError(
                f"{CAPA_RULE_ID} escalation thresholds must be non-negative"
            )
    elif rule_id == RISK_RULE_ID:
        _parse_single_non_negative_integer(rule)



def _prepare_evaluation_time(
    as_of: datetime | None,
) -> tuple[
    datetime,
    datetime,
    str,
    datetime,
]:
    settings = get_settings()

    reference_time = (
        as_of
        or datetime.now(timezone.utc)
    )

    if (
        reference_time.tzinfo is None
        or reference_time.utcoffset() is None
    ):
        raise ValueError(
            "as_of must include timezone information"
        )

    utc_aware = reference_time.astimezone(
        timezone.utc
    )

    utc_naive_for_mysql = utc_aware.replace(
        tzinfo=None
    )

    business_timezone = ZoneInfo(
        settings.app_timezone
    )

    local_time = utc_aware.astimezone(
        business_timezone
    )

    return (
        utc_aware,
        utc_naive_for_mysql,
        settings.app_timezone,
        local_time,
    )


def run_detection(
    session: Session,
    as_of: datetime | None = None,
    rule_ids: Collection[str] | None = None,
) -> dict[str, Any]:
    """
    Run all active detection rules, or only
    the requested rule IDs, without changing data.
    """
    (
        utc_aware,
        utc_naive_for_mysql,
        business_timezone,
        local_time,
    ) = _prepare_evaluation_time(as_of)

    active_rule_rows = (
        get_active_automation_rules(session)
    )

    rules = {
        str(rule["rule_id"]): rule
        for rule in active_rule_rows
    }

    rules = _select_requested_rules(
        rules,
        rule_ids,
    )

    for rule in rules.values():
        validate_rule_configuration(rule)

    permit_rule = _get_rule(
        rules,
        PERMIT_RULE_ID,
        "PERMIT",
    )

    certificate_rule = _get_rule(
        rules,
        CERTIFICATE_RULE_ID,
        "CERTIFICATE",
    )

    capa_rule = _get_rule(
        rules,
        CAPA_RULE_ID,
        "CAPA",
    )

    risk_rule = _get_rule(
        rules,
        RISK_RULE_ID,
        "RISK",
    )

    permits: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    capa: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []

    certificate_thresholds: tuple[
        int,
        ...
    ] = ()

    capa_escalation_days: tuple[
        int,
        ...
    ] = ()

    risk_review_age_days: int | None = None

    if permit_rule is not None:
        permit_grace_minutes = (
            _parse_single_non_negative_integer(
                permit_rule
            )
        )

        if permit_grace_minutes < 0:
            raise AutomationConfigurationError(
                f"{PERMIT_RULE_ID} requires a non-negative threshold"
            )


        permits = find_overdue_permits(
            session,
            utc_naive_for_mysql,
        )

    if certificate_rule is not None:
        certificate_thresholds = (
            _parse_non_negative_integers(
                certificate_rule
            )
        )

        certificates = find_certificate_alerts(
            session,
            local_time.date(),
            certificate_thresholds,
        )

    if capa_rule is not None:
        capa_escalation_days = (
            _parse_non_negative_integers(
                capa_rule
            )
        )

        capa = find_overdue_capa(
            session,
            local_time.date(),
        )

    if risk_rule is not None:
        risk_review_age_days = (
            _parse_single_non_negative_integer(
                risk_rule
            )
        )

        risks = find_stale_high_risks(
            session,
            local_time.date(),
            review_age_days=(
                risk_review_age_days
            ),
        )

    total_candidates = (
        len(permits)
        + len(certificates)
        + len(capa)
        + len(risks)
    )

    return {
        "status": "completed",
        "mode": "read_only_detection",
        "evaluated_at_utc": (
            utc_aware.isoformat()
        ),
        "business_timezone": (
            business_timezone
        ),
        "business_datetime": (
            local_time.isoformat()
        ),
        "business_date": (
            local_time.date().isoformat()
        ),
        "enabled_rule_ids": sorted(rules),
        "thresholds": {
            "certificate_days": list(
                certificate_thresholds
            ),
            "capa_escalation_days": list(
                capa_escalation_days
            ),
            "risk_review_age_days": (
                risk_review_age_days
            ),
        },
        "summary": {
            "overdue_permits": len(permits),
            "certificate_alerts": len(
                certificates
            ),
            "overdue_capa": len(capa),
            "stale_high_risks": len(risks),
            "total_candidates": (
                total_candidates
            ),
        },
        "candidates": {
            "permits": permits,
            "certificates": certificates,
            "capa": capa,
            "risks": risks,
        },
    }


def run_rule_detection(
    session: Session,
    rule_id: str,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """
    Run one active automation rule only.

    This function is used by APScheduler so every
    rule runs according to its own cron schedule.
    """
    return run_detection(
        session=session,
        as_of=as_of,
        rule_ids=(rule_id,),
    )
