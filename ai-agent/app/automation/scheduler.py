"""APScheduler controller for read-only detection and safe event delivery.

Every job follows this safe order:

1. read HSE data using one read-only MySQL session;
2. roll back and close that session;
3. build deterministic event envelopes in memory;
4. pass them to the explicitly configured dispatcher.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from time import monotonic
from typing import Any, NoReturn
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.automation.dispatcher import (
    DispatchResult,
    DryRunEventDispatcher,
    EventDispatcher,
)
from app.automation.events import build_automation_events
from app.automation.repository import get_active_automation_rules
from app.automation.service import (
    AutomationConfigurationError,
    SUPPORTED_RULE_IDS,
    run_rule_detection,
    validate_rule_configuration,
)
from app.database import SessionLocal


logger = logging.getLogger(__name__)

RULE_JOB_PREFIX = "automation-rule:"
DEFAULT_MISFIRE_GRACE_SECONDS = 3600


class AutomationJobExecutionError(RuntimeError):
    """Raised when a scheduled automation job cannot finish safely."""


class AutomationScheduleRefreshError(RuntimeError):
    """Raised when the initial schedule configuration cannot be loaded."""


def _default_clock() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(timezone.utc)


def _trigger_signature(
    trigger: CronTrigger,
) -> tuple[str, tuple[str, ...]]:
    """Create a stable value used to compare two cron triggers."""

    return (
        str(trigger.timezone),
        tuple(str(field) for field in trigger.fields),
    )


def _job_failure(
    *,
    rule_id: str,
    stage: str,
    error: Exception,
) -> NoReturn:
    """Log only safe metadata and expose one stable public exception."""

    logger.error(
        "automation_job_failed "
        "rule_id=%s stage=%s error_type=%s",
        rule_id,
        stage,
        type(error).__name__,
    )

    raise AutomationJobExecutionError(
        f"Automation job failed during {stage}"
    ) from None


class AutomationSchedulerController:
    """Create, update, remove, and execute automation rule jobs."""

    def __init__(
        self,
        scheduler: BaseScheduler,
        session_factory: Callable[[], Session] = SessionLocal,
        detector: Callable[..., dict[str, Any]] = run_rule_detection,
        clock: Callable[[], datetime] = _default_clock,
        event_builder: Callable[
            [Mapping[str, Any]],
            list[dict[str, Any]],
        ] = build_automation_events,
        dispatcher: EventDispatcher | None = None,
    ) -> None:
        self._scheduler = scheduler
        self._session_factory = session_factory
        self._detector = detector
        self._clock = clock
        self._event_builder = event_builder
        self._dispatcher = (
            dispatcher
            if dispatcher is not None
            else DryRunEventDispatcher()
        )

    def refresh_schedules(
        self,
        *,
        fail_fast: bool = False,
    ) -> int:
        """Reload active schedules from MySQL.

        If a later refresh fails, existing jobs are kept unchanged.
        During worker startup, fail_fast=True makes configuration
        problems stop the worker instead of starting it incorrectly.
        """

        try:
            with self._session_factory() as session:
                rules = get_active_automation_rules(session)
                session.rollback()

            return self.reconcile(rules)
        except Exception as exc:
            logger.error(
                "automation_schedule_refresh_failed error_type=%s",
                type(exc).__name__,
            )

            if fail_fast:
                raise AutomationScheduleRefreshError(
                    "Unable to load valid automation schedules"
                ) from None

            # A periodic refresh must never destroy the last-known-good
            # schedule when the database temporarily contains bad config.
            return len(self.scheduled_rule_job_ids())

    def reconcile(
        self,
        rules: Iterable[Mapping[str, Any]],
    ) -> int:
        """Make scheduled jobs match the active database rules."""

        # Build and validate the complete desired schedule before mutating
        # APScheduler. This makes reconciliation atomic from the worker's
        # point of view: one bad rule keeps every existing job unchanged.
        prepared_rules: dict[
            str,
            tuple[str, CronTrigger],
        ] = {}

        for rule in rules:
            rule_id = str(rule.get("rule_id") or "").strip()

            if rule_id not in SUPPORTED_RULE_IDS:
                logger.warning(
                    "automation_schedule_ignored reason=unsupported_rule"
                )
                continue

            try:
                validate_rule_configuration(rule)
                schedule_cron = str(
                    rule.get("schedule_cron") or ""
                ).strip()
                timezone_name = str(
                    rule.get("timezone") or ""
                ).strip()
                rule_timezone = ZoneInfo(timezone_name)
                trigger = CronTrigger.from_crontab(
                    schedule_cron,
                    timezone=rule_timezone,
                )
            except (
                AutomationConfigurationError,
                ValueError,
                ZoneInfoNotFoundError,
            ) as exc:
                logger.error(
                    "automation_schedule_invalid "
                    "rule_id=%s error_type=%s",
                    rule_id,
                    type(exc).__name__,
                )
                raise AutomationConfigurationError(
                    f"Invalid automation schedule for {rule_id}"
                ) from None

            job_id = f"{RULE_JOB_PREFIX}{rule_id}"

            if job_id in prepared_rules:
                raise AutomationConfigurationError(
                    f"Duplicate automation schedule for {rule_id}"
                )

            prepared_rules[job_id] = (rule_id, trigger)

        existing_jobs = {
            job.id: job
            for job in self._scheduler.get_jobs()
            if job.id.startswith(RULE_JOB_PREFIX)
        }

        desired_job_ids = set(prepared_rules)

        for job_id, (rule_id, trigger) in prepared_rules.items():
            existing_job = existing_jobs.get(job_id)

            if existing_job is None:
                self._scheduler.add_job(
                    self.run_rule,
                    trigger=trigger,
                    args=(rule_id,),
                    id=job_id,
                    name=job_id,
                    coalesce=True,
                    max_instances=1,
                    misfire_grace_time=(
                        DEFAULT_MISFIRE_GRACE_SECONDS
                    ),
                )

                logger.info(
                    "automation_schedule_added rule_id=%s",
                    rule_id,
                )
                continue

            trigger_changed = (
                not isinstance(existing_job.trigger, CronTrigger)
                or _trigger_signature(existing_job.trigger)
                != _trigger_signature(trigger)
            )

            if trigger_changed:
                self._scheduler.reschedule_job(
                    job_id,
                    trigger=trigger,
                )

                logger.info(
                    "automation_schedule_updated rule_id=%s",
                    rule_id,
                )

        stale_job_ids = set(existing_jobs) - desired_job_ids

        for job_id in stale_job_ids:
            self._scheduler.remove_job(job_id)

            logger.info(
                "automation_schedule_removed job_id=%s",
                job_id,
            )

        return len(desired_job_ids)

    def run_rule(
        self,
        rule_id: str,
    ) -> dict[str, Any]:
        """Detect, close MySQL, plan events, then dispatch safely."""

        if rule_id not in SUPPORTED_RULE_IDS:
            raise AutomationJobExecutionError(
                "Scheduled job uses an unsupported rule"
            )

        started_at = monotonic()

        # Detection is the only stage allowed to hold a database session.
        # The `with` block must finish before event planning or dispatch.
        try:
            evaluation_time = self._clock()

            with self._session_factory() as session:
                try:
                    detection_result = self._detector(
                        session,
                        rule_id,
                        evaluation_time,
                    )
                finally:
                    session.rollback()
        except Exception as exc:
            _job_failure(
                rule_id=rule_id,
                stage="detection",
                error=exc,
            )

        try:
            events = self._event_builder(detection_result)
        except Exception as exc:
            _job_failure(
                rule_id=rule_id,
                stage="event_planning",
                error=exc,
            )

        try:
            dispatch_result: DispatchResult = (
                self._dispatcher.dispatch(events)
            )
        except Exception as exc:
            _job_failure(
                rule_id=rule_id,
                stage="dispatch",
                error=exc,
            )

        summary = detection_result.get("summary", {})
        candidate_count = int(
            summary.get("total_candidates", 0)
        )
        duration_ms = int(
            (monotonic() - started_at) * 1000
        )

        logger.info(
            "automation_job_completed "
            "rule_id=%s candidates=%d events=%d "
            "mode=%s delivered=%d duration_ms=%d",
            rule_id,
            candidate_count,
            dispatch_result.planned_count,
            dispatch_result.mode,
            dispatch_result.delivered_count,
            duration_ms,
        )

        # Keep the detector's result immutable for injected fakes and add
        # only a small, non-sensitive aggregate summary to the job result.
        return {
            **detection_result,
            "action_summary": dispatch_result.as_dict(),
        }

    def scheduled_rule_job_ids(self) -> list[str]:
        """Return current rule job IDs for tests and diagnostics."""

        return sorted(
            job.id
            for job in self._scheduler.get_jobs()
            if job.id.startswith(RULE_JOB_PREFIX)
        )

    @property
    def delivery_mode(self) -> str:
        """Expose the non-sensitive dispatcher mode for diagnostics."""

        return self._dispatcher.mode

    def close(self) -> None:
        """Release dispatcher resources after scheduled work has stopped."""

        close = getattr(self._dispatcher, "close", None)
        if callable(close):
            close()
