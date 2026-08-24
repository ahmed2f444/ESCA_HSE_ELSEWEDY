"""Fail-closed dispatchers for planned automation events.

Dry-run is the safe default. The Spring implementation is constructed only
by the worker's explicitly gated live-mode factory. Both implementations
validate the complete batch before performing any per-event work.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from app.automation.spring_client import SpringAutomationClient


logger = logging.getLogger(__name__)

DRY_RUN_MODE = "dry_run"
SPRING_MODE = "spring"


class AutomationDispatchError(ValueError):
    """Raised when an event batch is unsafe or malformed."""


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
