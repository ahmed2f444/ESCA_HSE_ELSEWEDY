import pytest
from datetime import datetime, timezone, date, timedelta
from unittest.mock import MagicMock, patch

from app.automation.repository import (
    DEFAULT_CERTIFICATE_THRESHOLDS,
    _certificate_alert_code,
    _normalise_thresholds,
)
from app.automation.service import (
    run_detection,
    validate_rule_configuration,
    AutomationConfigurationError,
    _prepare_evaluation_time,
)
from app.automation.events import (
    build_automation_events,
    _event_digest,
)
from app.automation.dispatcher import (
    DryRunEventDispatcher,
    DatabaseEventDispatcher,
    SpringEventDispatcher,
    DispatchResult,
)
from app.automation.scheduler import AutomationSchedulerController
from app.database import SessionLocal
from apscheduler.schedulers.background import BackgroundScheduler


def test_validate_rule_configuration():
    # Valid rule
    valid_rule = {
        "rule_id": "AUT-001",
        "entity_type": "PERMIT",
        "threshold_value": "24",
        "schedule_cron": "0 */2 * * *",
        "timezone": "Africa/Cairo"
    }
    validate_rule_configuration(valid_rule)

    # Valid certificate rule with list/comma thresholds
    valid_cert_rule = {
        "rule_id": "AUT-002",
        "entity_type": "CERTIFICATE",
        "threshold_value": "30,14,7,0",
        "schedule_cron": "0 8 * * *",
        "timezone": "Africa/Cairo"
    }
    validate_rule_configuration(valid_cert_rule)

    # Invalid entity type
    invalid_rule = {
        "rule_id": "AUT-001",
        "entity_type": "WRONG_TYPE",
        "threshold_value": "24",
    }
    with pytest.raises(AutomationConfigurationError):
        validate_rule_configuration(invalid_rule)


def test_certificate_expiry_boundary_calculations():
    """Verify threshold detection across all boundary cases (-1, 0, 7, 14, 30, 60 days)."""
    thresholds = _normalise_thresholds((30, 14, 7, 0))
    assert thresholds == (0, 7, 14, 30)

    # Past expiry (< 0) -> CERTIFICATE_EXPIRED
    assert _certificate_alert_code(-10, thresholds) == "CERTIFICATE_EXPIRED"
    assert _certificate_alert_code(-1, thresholds) == "CERTIFICATE_EXPIRED"

    # Due today (0) -> CERTIFICATE_DUE_0_DAYS
    assert _certificate_alert_code(0, thresholds) == "CERTIFICATE_DUE_0_DAYS"

    # Within 7 days (1..7) -> CERTIFICATE_DUE_7_DAYS
    assert _certificate_alert_code(1, thresholds) == "CERTIFICATE_DUE_7_DAYS"
    assert _certificate_alert_code(5, thresholds) == "CERTIFICATE_DUE_7_DAYS"
    assert _certificate_alert_code(7, thresholds) == "CERTIFICATE_DUE_7_DAYS"

    # Within 14 days (8..14) -> CERTIFICATE_DUE_14_DAYS
    assert _certificate_alert_code(8, thresholds) == "CERTIFICATE_DUE_14_DAYS"
    assert _certificate_alert_code(10, thresholds) == "CERTIFICATE_DUE_14_DAYS"
    assert _certificate_alert_code(14, thresholds) == "CERTIFICATE_DUE_14_DAYS"

    # Within 30 days (15..30) -> CERTIFICATE_DUE_30_DAYS
    assert _certificate_alert_code(15, thresholds) == "CERTIFICATE_DUE_30_DAYS"
    assert _certificate_alert_code(25, thresholds) == "CERTIFICATE_DUE_30_DAYS"
    assert _certificate_alert_code(30, thresholds) == "CERTIFICATE_DUE_30_DAYS"

    # Beyond maximum threshold (> 30) -> None
    assert _certificate_alert_code(31, thresholds) is None
    assert _certificate_alert_code(60, thresholds) is None


def test_certificate_idempotency_progression_and_deduplication():
    """Verify progressive multi-stage escalations and intra-day deduplication."""
    # 1. Intra-day deduplication: Same day, same bracket -> identical hash
    digest_30d_run1 = _event_digest(
        rule_id="AUT-002",
        entity_type="CERTIFICATE",
        entity_id="CERT-100",
        alert_code="CERTIFICATE_DUE_30_DAYS",
        occurrence_marker="2026-09-28|bracket=due_30_days|date=2026-08-29",
    )
    digest_30d_run2 = _event_digest(
        rule_id="AUT-002",
        entity_type="CERTIFICATE",
        entity_id="CERT-100",
        alert_code="CERTIFICATE_DUE_30_DAYS",
        occurrence_marker="2026-09-28|bracket=due_30_days|date=2026-08-29",
    )
    assert digest_30d_run1 == digest_30d_run2

    # 2. Stage Progression: 30d -> 14d -> 7d -> 0d -> expired -> distinct hashes
    digest_14d = _event_digest(
        rule_id="AUT-002",
        entity_type="CERTIFICATE",
        entity_id="CERT-100",
        alert_code="CERTIFICATE_DUE_14_DAYS",
        occurrence_marker="2026-09-28|bracket=due_14_days|date=2026-09-14",
    )
    digest_7d = _event_digest(
        rule_id="AUT-002",
        entity_type="CERTIFICATE",
        entity_id="CERT-100",
        alert_code="CERTIFICATE_DUE_7_DAYS",
        occurrence_marker="2026-09-28|bracket=due_7_days|date=2026-09-21",
    )
    digest_0d = _event_digest(
        rule_id="AUT-002",
        entity_type="CERTIFICATE",
        entity_id="CERT-100",
        alert_code="CERTIFICATE_DUE_0_DAYS",
        occurrence_marker="2026-09-28|bracket=due_0_days|date=2026-09-28",
    )
    digest_expired = _event_digest(
        rule_id="AUT-002",
        entity_type="CERTIFICATE",
        entity_id="CERT-100",
        alert_code="CERTIFICATE_EXPIRED",
        occurrence_marker="2026-09-28|bracket=expired|date=2026-09-29",
    )

    all_digests = {digest_30d_run1, digest_14d, digest_7d, digest_0d, digest_expired}
    assert len(all_digests) == 5, "Each stage progression must produce a distinct idempotency digest"


def test_timezone_normalization():
    """Verify timezone evaluation normalizes UTC to business timezone without date drift."""
    utc_time = datetime(2026, 8, 29, 23, 0, 0, tzinfo=timezone.utc)
    utc_aware, utc_naive, tz_name, local_time = _prepare_evaluation_time(utc_time)
    
    assert utc_aware == utc_time
    assert utc_naive == datetime(2026, 8, 29, 23, 0, 0)
    assert tz_name == "Africa/Cairo"
    # Africa/Cairo is UTC+3 in August, so 23:00 UTC = 02:00 next day in Cairo
    assert local_time.date() == date(2026, 8, 30)


def test_automation_detection_service():
    with SessionLocal() as session:
        result = run_detection(session)
        assert result["status"] == "completed"
        assert result["mode"] == "read_only_detection"
        assert "summary" in result
        assert "candidates" in result
        assert "AUT-001" in result["enabled_rule_ids"]
        assert "AUT-004" in result["enabled_rule_ids"]


def test_event_planning_contract_compliance():
    with SessionLocal() as session:
        detection_result = run_detection(session)
        events = build_automation_events(detection_result)
        
        for ev in events:
            assert ev["schema_version"] == "1.0"
            assert ev["event_id"].startswith("evt_")
            assert len(ev["event_id"]) == 36  # "evt_" + 32 hex chars
            assert ev["idempotency_key"].startswith("hse-automation:v1:")
            assert ev["rule_id"] in {"AUT-001", "AUT-002", "AUT-003", "AUT-004"}
            assert "payload" in ev
            assert isinstance(ev["payload"], dict)
            
            # Ensure no forbidden PII fields in payload
            for forbidden in ["employee_name", "email", "description", "password"]:
                assert forbidden not in ev["payload"]


def test_dry_run_dispatcher():
    dispatcher = DryRunEventDispatcher()
    sample_events = [
        {
            "schema_version": "1.0",
            "event_id": "evt_11111111111111111111111111111111",
            "idempotency_key": "hse-automation:v1:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "rule_id": "AUT-001",
            "entity_type": "PERMIT",
            "entity_id": "1",
            "alert_code": "PERMIT_OVERDUE",
            "action": "FLAG_OVERDUE_PERMIT",
            "delivery_mode": "dry_run",
            "evaluated_at_utc": "2026-08-24T12:00:00Z",
            "business_date": "2026-08-24",
            "payload": {"permit_id": 1, "status": "ACTIVE", "minutes_overdue": 60}
        }
    ]
    res = dispatcher.dispatch(sample_events)
    assert isinstance(res, DispatchResult)
    assert res.mode == "dry_run"
    assert res.planned_count == 1
    assert res.delivered_count == 0


def test_scheduler_reconciliation():
    sched = BackgroundScheduler()
    ctrl = AutomationSchedulerController(scheduler=sched)
    count = ctrl.refresh_schedules()
    assert count >= 4  # Should reconcile at least the 4 core rules AUT-001 to AUT-004
    job_ids = ctrl.scheduled_rule_job_ids()
    assert "automation-rule:AUT-001" in job_ids
    assert "automation-rule:AUT-004" in job_ids
