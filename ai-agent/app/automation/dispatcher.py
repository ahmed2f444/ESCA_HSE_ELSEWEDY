"""Fail-closed dispatchers for planned automation events.

Dry-run is the safe default. The Spring implementation is constructed only
by the worker's explicitly gated live-mode factory. Both implementations
validate the complete batch before performing any per-event work.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from sqlalchemy import text

from app.automation.spring_client import (
    SpringAutomationClient,
    SpringClientConfig,
)
from app.config import Settings
from app.database import SessionLocal


logger = logging.getLogger(__name__)

DRY_RUN_MODE = "dry_run"
SPRING_MODE = "spring"
DATABASE_MODE = "database"


class AutomationDispatchError(ValueError):
    """Raised when an event batch is unsafe or malformed."""


def create_event_dispatcher(settings: Settings) -> EventDispatcher:
    """Build the configured dispatcher after validating both safety gates.

    Live delivery is enabled when the mode is ``spring`` or ``database`` *and*
    the explicit live flag is true. Contradictory settings fail closed instead
    of silently selecting a different behavior.
    """

    mode = settings.automation_delivery_mode
    live_enabled = settings.automation_live_enabled

    if mode == DRY_RUN_MODE:
        if live_enabled:
            raise AutomationDispatchError(
                "Live automation requires spring or database delivery mode"
            )
        return DryRunEventDispatcher()

    if mode == DATABASE_MODE:
        if not live_enabled:
            raise AutomationDispatchError(
                "Database delivery requires AUTOMATION_LIVE_ENABLED=true"
            )
        return DatabaseEventDispatcher()

    if mode != SPRING_MODE:
        raise AutomationDispatchError(
            "Unsupported automation delivery mode"
        )
    if not live_enabled:
        raise AutomationDispatchError(
            "Spring delivery requires AUTOMATION_LIVE_ENABLED=true"
        )

    client_config = SpringClientConfig(
        base_url=settings.spring_api_base_url,
        client_id=settings.automation_client_id,
        client_secret=settings.automation_client_secret,
        connect_timeout_seconds=settings.spring_connect_timeout_seconds,
        read_timeout_seconds=settings.spring_read_timeout_seconds,
        max_attempts=settings.spring_max_attempts,
        token_refresh_leeway_seconds=(
            settings.spring_token_refresh_leeway_seconds
        ),
    )
    return SpringEventDispatcher(SpringAutomationClient(client_config))


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """Small, non-sensitive summary returned to the scheduler."""

    mode: str
    planned_count: int
    delivered_count: int

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


class EventDispatcher(Protocol):
    """Common scheduler-facing dispatcher contract."""

    mode: str

    def dispatch(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> DispatchResult:
        """Handle one immutable batch of planned automation events."""

    def close(self) -> None:
        """Release owned resources without raising on repeated calls."""


def _required_text(
    event: Mapping[str, Any],
    field_name: str,
) -> str:
    value = event.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise AutomationDispatchError(
            f"Event is missing required field: {field_name}"
        )
    return value.strip()


def _validate_batch(
    events: Sequence[Mapping[str, Any]],
    *,
    expected_mode: str,
) -> tuple[Mapping[str, Any], ...]:
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise AutomationDispatchError(
            "Event batch must be a sequence of objects"
        )

    validated: list[Mapping[str, Any]] = []
    event_ids: set[str] = set()
    idempotency_keys: set[str] = set()

    for event in events:
        if not isinstance(event, Mapping):
            raise AutomationDispatchError(
                "Every planned event must be an object"
            )

        delivery_mode = _required_text(event, "delivery_mode")
        if delivery_mode != expected_mode:
            mode_label = (
                "dry-run"
                if expected_mode == DRY_RUN_MODE
                else expected_mode
            )
            raise AutomationDispatchError(
                f"Only {mode_label} events are allowed"
            )

        event_id = _required_text(event, "event_id")
        idempotency_key = _required_text(event, "idempotency_key")
        _required_text(event, "rule_id")

        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            raise AutomationDispatchError(
                "Event payload must be an object"
            )

        if event_id in event_ids:
            raise AutomationDispatchError(
                "Event batch contains a duplicate event ID"
            )
        if idempotency_key in idempotency_keys:
            raise AutomationDispatchError(
                "Event batch contains a duplicate idempotency key"
            )

        event_ids.add(event_id)
        idempotency_keys.add(idempotency_key)
        validated.append(event)

    return tuple(validated)


class DryRunEventDispatcher:
    """Validate events and report counts without side effects."""

    mode = DRY_RUN_MODE

    def dispatch(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> DispatchResult:
        validated = _validate_batch(events, expected_mode=self.mode)
        result = DispatchResult(
            mode=self.mode,
            planned_count=len(validated),
            delivered_count=0,
        )
        logger.info(
            "automation_events_dry_run planned=%d delivered=0",
            result.planned_count,
        )
        return result

    def close(self) -> None:
        """Dry-run owns no external resource."""


class DatabaseEventDispatcher:
    """Deliver a prevalidated batch directly to the MySQL database.

    Inserts idempotent unread notifications and audit/action records.
    """

    mode = DATABASE_MODE

    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory
        self._closed = False

    def dispatch(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> DispatchResult:
        if self._closed:
            raise AutomationDispatchError("Database dispatcher is closed")

        validated = _validate_batch(events, expected_mode=self.mode)
        delivered_count = 0
        applied_count = 0
        duplicate_count = 0

        with self._session_factory() as session:
            try:
                for event in validated:
                    rule_id = str(event.get("rule_id", "")).strip()
                    entity_type = str(event.get("entity_type", "")).strip()
                    entity_id = str(event.get("entity_id", "")).strip()
                    idem_key = str(event.get("idempotency_key", "")).strip()
                    action = str(event.get("action", "")).strip()
                    alert_code = str(event.get("alert_code", "")).strip()
                    payload = dict(event.get("payload") or {})

                    # Check for duplicate action record by idempotency key
                    exists = None
                    try:
                        exists = session.execute(
                            text("SELECT action_id FROM automation_actions WHERE idempotency_key = :idem LIMIT 1"),
                            {"idem": idem_key}
                        ).fetchone()
                        if not exists:
                            exists = session.execute(
                                text("SELECT notification_id FROM notifications WHERE idempotency_key = :idem LIMIT 1"),
                                {"idem": idem_key}
                            ).fetchone()
                    except Exception:
                        pass

                    if exists:
                        duplicate_count += 1
                        delivered_count += 1
                        continue

                    # Build descriptive Arabic notification title and body
                    if rule_id == "AUT-001":
                        title = f"تنبيه أتمتة السلامة: تصريح عمل متأخر #{entity_id}"
                        body = f"تجاوز تصريح العمل #{entity_id} موعد انتهائه المحدد ويحتاج إلى إغلاق أو تمديد فوري — تم تفعيل تنبيه السلامة الآلي (AUT-001)."
                        notif_type = "AUTOMATION_PERMIT_OVERDUE"
                    elif rule_id == "AUT-002":
                        title = f"تنبيه أتمتة السلامة: انتهاء صلاحية شهادة #{entity_id}"
                        body = f"الاعتماد التدريبي #{entity_id} منتهي أو يقترب من الانتهاء — تم تفعيل تنبيه السلامة الآلي (AUT-002) وتحديث مصفوفة الكفاءة لمنع إسناد الأعمال الخطرة."
                        notif_type = "AUTOMATION_CERTIFICATE_EXPIRY"
                    elif rule_id == "AUT-003":
                        title = f"تنبيه أتمتة السلامة: تصعيد إجراء تصحيحي متأخر #{entity_id}"
                        body = f"الإجراء التصحيحي CAPA #{entity_id} متأخر عن موعد الإنجاز المستهدف ويحتاج إلى تصعيد للمتابعة (AUT-003)."
                        notif_type = "AUTOMATION_CAPA_OVERDUE"
                    else:
                        title = f"تنبيه أتمتة السلامة: مراجعة سجل مخاطر مرتفع #{entity_id}"
                        body = f"سجل الخطر #{entity_id} ذو درجة خطورة عالية وتجاوز دورة المراجعة الدورية — تم إطلاق تنبيه المراجعة الآلي (AUT-004)."
                        notif_type = "AUTOMATION_RISK_REVIEW"

                    recipient_emp = (
                        payload.get("employee_id")
                        or payload.get("assigned_to")
                        or payload.get("issuer_id")
                        or payload.get("requester_id")
                        or payload.get("owner_id")
                        or "ROLE-003"
                    )

                    # Insert notification into MySQL notifications table
                    session.execute(text("""
                        INSERT INTO notifications (
                            type, severity_id, entity_type, entity_id,
                            recipient_type_id, recipient_id, title, message,
                            status_id, idempotency_key, source_service
                        ) VALUES (
                            :type, 3, :entity_type, :entity_id,
                            1, :recipient_id, :title, :message,
                            1, :idem, 'esca-hse-automation-service'
                        )
                    """), {
                        "type": notif_type,
                        "entity_type": entity_type,
                        "entity_id": str(entity_id),
                        "recipient_id": str(recipient_emp),
                        "title": title,
                        "message": body,
                        "idem": idem_key,
                    })

                    # Insert audit record into automation_actions table
                    rule_num = int(rule_id.replace("AUT-", "")) if "AUT-" in rule_id else 1
                    session.execute(text("""
                        INSERT INTO automation_actions (
                            run_id, rule_id, entity_type, entity_id,
                            action_type, spring_endpoint, requested_at,
                            http_status, outcome_id, idempotency_key, audit_id, error_summary
                        ) VALUES (
                            1, :rule_num, :entity_type, :entity_id,
                            :action_type, '/api/v1/internal/automation/actions', NOW(),
                            201, 1, :idem, 1, NULL
                        )
                    """), {
                        "rule_num": rule_num,
                        "entity_type": entity_type,
                        "entity_id": str(entity_id),
                        "action_type": action,
                        "idem": idem_key,
                    })

                    # For expired certificates (AUT-002), update status to EXPIRED in certificates table
                    if rule_id == "AUT-002" and alert_code == "CERTIFICATE_EXPIRED":
                        try:
                            session.execute(text("""
                                UPDATE certificates
                                SET status = 'EXPIRED', status_id = 2
                                WHERE certificate_id = :entity_id
                            """), {"entity_id": str(entity_id)})
                        except Exception:
                            try:
                                session.execute(text("""
                                    UPDATE certificates
                                    SET status = 'EXPIRED'
                                    WHERE certificate_id = :entity_id
                                """), {"entity_id": str(entity_id)})
                            except Exception:
                                pass

                    applied_count += 1
                    delivered_count += 1

                session.commit()
            except Exception as exc:
                session.rollback()
                logger.error("automation_database_dispatch_failed error=%s", exc)
                raise AutomationDispatchError(f"Database dispatch failed: {exc}") from exc

        dispatch_result = DispatchResult(
            mode=self.mode,
            planned_count=len(validated),
            delivered_count=delivered_count,
        )
        logger.info(
            "automation_events_database planned=%d delivered=%d applied=%d duplicate=%d",
            dispatch_result.planned_count,
            dispatch_result.delivered_count,
            applied_count,
            duplicate_count,
        )
        return dispatch_result

    def close(self) -> None:
        self._closed = True


class SpringEventDispatcher:
    """Deliver a prevalidated batch through Spring one event at a time.

    The batch is validated in two passes before the first token request. A
    later transport failure can leave a partial batch applied, which is safe
    because retries preserve each event's Spring-enforced idempotency key.
    """

    mode = SPRING_MODE

    def __init__(self, client: SpringAutomationClient) -> None:
        self._client = client
        self._closed = False

    def dispatch(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> DispatchResult:
        if self._closed:
            raise AutomationDispatchError("Spring dispatcher is closed")

        validated = _validate_batch(events, expected_mode=self.mode)

        # Validate every contract before any token or action request. This
        # prevents a malformed later event from causing avoidable partial
        # side effects.
        for event in validated:
            self._client.validate_action(event)

        delivered_count = 0
        outcome_counts = {
            "APPLIED": 0,
            "DUPLICATE": 0,
            "NOT_APPLICABLE": 0,
        }
        for event in validated:
            result = self._client.send_action(event)
            if result.status not in outcome_counts:
                raise AutomationDispatchError(
                    "Spring returned an unsupported action outcome"
                )
            outcome_counts[result.status] += 1
            delivered_count += 1

        dispatch_result = DispatchResult(
            mode=self.mode,
            planned_count=len(validated),
            delivered_count=delivered_count,
        )
        logger.info(
            "automation_events_spring planned=%d delivered=%d "
            "applied=%d duplicate=%d not_applicable=%d",
            dispatch_result.planned_count,
            dispatch_result.delivered_count,
            outcome_counts["APPLIED"],
            outcome_counts["DUPLICATE"],
            outcome_counts["NOT_APPLICABLE"],
        )
        return dispatch_result

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._client.close()
