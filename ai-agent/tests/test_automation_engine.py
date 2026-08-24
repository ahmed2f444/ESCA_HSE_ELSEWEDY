import pytest
from datetime import datetime, timezone, date
from unittest.mock import MagicMock, patch

from app.automation.service import run_detection, validate_rule_configuration, AutomationConfigurationError
from app.automation.events import build_automation_events
from app.automation.dispatcher import DryRunEventDispatcher, SpringEventDispatcher, DispatchResult
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

    # Invalid entity type
    invalid_rule = {
        "rule_id": "AUT-001",
        "entity_type": "WRONG_TYPE",
        "threshold_value": "24",
    }
    with pytest.raises(AutomationConfigurationError):
        validate_rule_configuration(invalid_rule)


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
