import json
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


DEFAULT_CERTIFICATE_THRESHOLDS = (30, 14, 7, 0)


def _fetch_all(
    session: Session,
    sql: str,
    parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run one SELECT query and return ordinary dictionaries."""
    rows = session.execute(text(sql), parameters).mappings().all()
    return [dict(row) for row in rows]


def get_active_automation_rules(
    session: Session,
) -> list[dict[str, Any]]:
    """Return the active automation rules owned by Member 4."""
    try:
        raw_rules = _fetch_all(
            session,
            """
            SELECT
                rule_id,
                rule_name,
                entity_type,
                schedule_cron,
                timezone,
                threshold_value
            FROM automation_rules
            WHERE (active_flag = 1 OR active_flag IS TRUE)
              AND entity_type IN (
                  'PERMIT',
                  'CERTIFICATE',
                  'CAPA',
                  'RISK'
              )
            ORDER BY rule_id
            """,
            {},
        )
    except Exception:
        raw_rules = _fetch_all(
            session,
            """
            SELECT
                rule_id,
                rule_name,
                entity_type,
                schedule_cron,
                conditions_json,
                active
            FROM automation_rules
            WHERE (active = 1 OR active IS TRUE OR active IS NULL)
              AND entity_type IN (
                  'PERMIT',
                  'CERTIFICATE',
                  'CAPA',
                  'RISK'
              )
            ORDER BY rule_id
            """,
            {},
        )

    mapping = {
        "PERMIT": "AUT-001",
        "CERTIFICATE": "AUT-002",
        "CAPA": "AUT-003",
        "RISK": "AUT-004",
    }
    default_thresholds = {
        "AUT-001": "24",
        "AUT-002": "30,14,7,0",
        "AUT-003": "1,3,7",
        "AUT-004": "30",
    }
    default_crons = {
        "AUT-001": "*/5 * * * *",
        "AUT-002": "0 8 * * *",
        "AUT-003": "0 9 * * *",
        "AUT-004": "0 7 * * 1",
    }

    normalized = []
    for r in raw_rules:
        rule_copy = dict(r)
        entity = rule_copy.get("entity_type")
        if entity in mapping:
            rule_copy["rule_id"] = mapping[entity]
        elif not isinstance(rule_copy.get("rule_id"), str):
            rule_copy["rule_id"] = f"AUT-{int(rule_copy['rule_id']):03d}"

        rule_id = rule_copy["rule_id"]

        if not rule_copy.get("threshold_value"):
            cond_raw = rule_copy.get("conditions_json")
            if cond_raw:
                try:
                    cond = json.loads(cond_raw) if isinstance(cond_raw, str) else cond_raw
                    if "days" in cond and isinstance(cond["days"], list):
                        rule_copy["threshold_value"] = ",".join(str(d) for d in cond["days"])
                    elif "review_age_days" in cond:
                        rule_copy["threshold_value"] = str(cond["review_age_days"])
                    elif "grace_minutes" in cond:
                        rule_copy["threshold_value"] = str(cond["grace_minutes"])
                except Exception:
                    pass

        if not rule_copy.get("threshold_value"):
            rule_copy["threshold_value"] = default_thresholds.get(rule_id, "0")

        if not rule_copy.get("timezone"):
            rule_copy["timezone"] = "Africa/Cairo"

        if not rule_copy.get("schedule_cron"):
            rule_copy["schedule_cron"] = default_crons.get(rule_id, "0 0 * * *")

        normalized.append(rule_copy)

    return normalized


def find_overdue_permits(
    session: Session,
    as_of_utc: datetime,
) -> list[dict[str, Any]]:
    """Find ACTIVE or APPROVED permits whose UTC expiry time has passed."""
    if as_of_utc.tzinfo is not None:
        raise ValueError("as_of_utc must be a naive UTC datetime")

    return _fetch_all(
        session,
        """
        SELECT
            p.permit_id,
            COALESCE(z.department_id, p.zone_id, 1) AS department_id,
            p.zone_id,
            p.requester_id,
            p.issuer_id,
            p.expiry_at,
            COALESCE(rl.name, 'MEDIUM') AS risk_level,
            COALESCE(st.name, 'ACTIVE') AS status,
            TIMESTAMPDIFF(
                MINUTE,
                p.expiry_at,
                :as_of_utc
            ) AS minutes_overdue,
            'PERMIT_OVERDUE' AS alert_code
        FROM permits AS p
        LEFT JOIN permit_statuses AS st ON st.permit_status_id = p.status_id
        LEFT JOIN permit_risk_levels AS rl ON rl.permit_risk_level_id = p.risk_level_id
        LEFT JOIN zones AS z ON z.zone_id = p.zone_id
        WHERE (
            UPPER(st.name) IN ('ACTIVE', 'APPROVED')
            OR p.status_id IN (2, 3)
        )
          AND p.expiry_at <= :as_of_utc
        ORDER BY
            p.expiry_at,
            p.permit_id
        """,
        {"as_of_utc": as_of_utc},
    )


def _normalise_thresholds(
    thresholds: Sequence[int],
) -> tuple[int, ...]:
    normalised = tuple(
        sorted(
            {
                int(value)
                for value in thresholds
                if int(value) >= 0
            }
        )
    )

    if not normalised:
        raise ValueError(
            "At least one non-negative certificate threshold is required"
        )

    return normalised


def _certificate_alert_code(
    days_to_expiry: int,
    thresholds: tuple[int, ...],
) -> str | None:
    if days_to_expiry < 0:
        return "CERTIFICATE_EXPIRED"

    if days_to_expiry == 0 and 0 in thresholds:
        return "CERTIFICATE_DUE_0_DAYS"

    for threshold in thresholds:
        if threshold > 0 and days_to_expiry <= threshold:
            return f"CERTIFICATE_DUE_{threshold}_DAYS"

    return None


def find_certificate_alerts(
    session: Session,
    as_of_date: date,
    thresholds: Sequence[int] = DEFAULT_CERTIFICATE_THRESHOLDS,
) -> list[dict[str, Any]]:
    """
    Find expired certificates and certificates inside the configured alert windows.
    """
    normalised_thresholds = _normalise_thresholds(thresholds)
    expiry_limit = as_of_date + timedelta(days=max(normalised_thresholds))

    rows = _fetch_all(
        session,
        """
        SELECT
            c.certificate_id,
            c.employee_id,
            c.course_id,
            c.expiry_date,
            COALESCE(st.name, 'VALID') AS status,
            COALESCE(c.manager_id, e.manager_id) AS manager_id,
            DATEDIFF(
                DATE(c.expiry_date),
                :as_of_date
            ) AS days_to_expiry
        FROM certificates AS c
        LEFT JOIN certificate_statuses AS st ON st.certificate_status_id = c.status_id
        LEFT JOIN employees AS e ON e.employee_id = c.employee_id
        WHERE c.expiry_date IS NOT NULL
          AND (
              UPPER(st.name) IN ('VALID', 'EXPIRED', 'RENEWAL_BOOKED', 'ACTIVE')
              OR c.status_id IS NOT NULL
          )
          AND DATE(c.expiry_date) <= :expiry_limit
        ORDER BY
            c.expiry_date,
            c.certificate_id
        """,
        {
            "as_of_date": as_of_date,
            "expiry_limit": expiry_limit,
        },
    )

    alerts: list[dict[str, Any]] = []
    for row in rows:
        days_to_expiry = int(row["days_to_expiry"])
        alert_code = _certificate_alert_code(days_to_expiry, normalised_thresholds)
        if alert_code is not None:
            row["alert_code"] = alert_code
            alerts.append(row)

    return alerts


def find_overdue_capa(
    session: Session,
    as_of_date: date,
) -> list[dict[str, Any]]:
    """
    Find OPEN or IN_PROGRESS CAPAs whose due date has passed.
    """
    return _fetch_all(
        session,
        """
        SELECT
            c.capa_id,
            c.incident_id,
            c.finding_id,
            COALESCE(pr.name, 'MEDIUM') AS priority,
            c.assigned_to,
            c.due_date,
            COALESCE(st.name, 'OPEN') AS status,
            DATEDIFF(
                :as_of_date,
                DATE(c.due_date)
            ) AS days_overdue,
            'CAPA_OVERDUE' AS alert_code
        FROM capa AS c
        LEFT JOIN capa_statuses AS st ON st.capa_status_id = c.status_id
        LEFT JOIN capa_priorities AS pr ON pr.capa_priority_id = c.priority_id
        WHERE c.due_date IS NOT NULL
          AND (
              UPPER(st.name) IN ('OPEN', 'IN_PROGRESS')
              OR c.status_id IN (1, 2)
          )
          AND DATE(c.due_date) < :as_of_date
        ORDER BY
            c.due_date,
            c.capa_id
        """,
        {"as_of_date": as_of_date},
    )


def find_stale_high_risks(
    session: Session,
    as_of_date: date,
    review_age_days: int = 30,
    minimum_score: int = 15,
) -> list[dict[str, Any]]:
    """
    Find active high risks that were never reviewed or have not been reviewed recently enough.
    """
    if review_age_days < 0:
        raise ValueError("review_age_days cannot be negative")

    if minimum_score < 1:
        raise ValueError("minimum_score must be positive")

    review_cutoff = as_of_date - timedelta(days=review_age_days)

    return _fetch_all(
        session,
        """
        SELECT
            r.risk_id,
            COALESCE(z.department_id, r.zone_id, 1) AS department_id,
            r.zone_id,
            r.inherent_score,
            r.risk_level,
            r.residual_score,
            r.owner_id,
            COALESCE(st.name, 'ACTIVE') AS status,
            r.last_reviewed_at,
            r.next_review_date,
            DATEDIFF(
                :as_of_date,
                DATE(COALESCE(r.last_reviewed_at, r.next_review_date, :review_cutoff))
            ) AS days_since_review,
            CASE
                WHEN r.last_reviewed_at IS NULL
                    THEN 'RISK_REVIEW_REQUIRED'
                ELSE 'RISK_REVIEW_OVERDUE'
            END AS alert_code
        FROM risk_register AS r
        LEFT JOIN risk_register_statuses AS st ON st.risk_register_status_id = r.status_id
        LEFT JOIN zones AS z ON z.zone_id = r.zone_id
        WHERE (
            UPPER(st.name) IN ('ACTIVE', 'OPEN')
            OR r.status_id = 1
        )
          AND r.inherent_score >= :minimum_score
          AND (
              r.last_reviewed_at IS NULL
              OR DATE(r.last_reviewed_at) <= :review_cutoff
          )
        ORDER BY
            r.inherent_score DESC,
            r.last_reviewed_at,
            r.risk_id
        """,
        {
            "as_of_date": as_of_date,
            "minimum_score": minimum_score,
            "review_cutoff": review_cutoff,
        },
    )
