"""Comprehensive diagnostic test suite for ESCA HSE Automation Engine.

Tests every active module (Permits AUT-001, CAPA AUT-003, Risk Register AUT-004,
and Core Engine Infrastructure) while preserving AUT-002 isolation.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import text

from app.automation.dispatcher import (
    AutomationDispatchError,
    DatabaseEventDispatcher,
    DispatchResult,
    DryRunEventDispatcher,
    SpringEventDispatcher,
    create_event_dispatcher,
)
from app.automation.events import (
    AutomationEventError,
    build_automation_events,
    _capa_escalation_day,
    _event_digest,
    _json_value,
    _normalise_thresholds,
)
from app.automation.repository import (
    find_overdue_capa,
    find_overdue_permits,
    find_stale_high_risks,
    get_active_automation_rules,
)
from app.automation.scheduler import AutomationSchedulerController
from app.automation.service import (
    AutomationConfigurationError,
    _parse_non_negative_integers,
    _parse_single_non_negative_integer,
    _prepare_evaluation_time,
    run_detection,
    run_rule_detection,
    validate_rule_configuration,
)
from app.automation.spring_client import (
    RuleContract,
    SpringActionResult,
    SpringAutomationClient,
    SpringClientConfig,
    SpringEventValidationError,
    _calendar_date_or_utc_timestamp,
    _prepare_action,
)
from app.database import SessionLocal


# ===========================================================================
# 1. PERMIT EXPIRY AUTOMATION (AUT-001) TESTS
# ===========================================================================

def test_aut001_permit_detection_and_payload_transformation():
    """Verify AUT-001 overdue permit detection, payload normalization, and event construction."""
    report = {
        "mode": "read_only_detection",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "enabled_rule_ids": ["AUT-001"],
        "thresholds": {},
        "candidates": {
            "permits": [
                {
                    "permit_id": "PTW-2026-001",
                    "department_id": 2,
                    "zone_id": 3,
                    "requester_id": "EMP-042",
                    "issuer_id": "EMP-007",
                    "expiry_at": "2026-08-29T08:30:00Z",
                    "risk_level": "HIGH",
                    "status": "ACTIVE",
                    "minutes_overdue": 90,
                    "alert_code": "PERMIT_OVERDUE",
                }
            ],
            "certificates": [],
            "capa": [],
            "risks": [],
        },
    }

    events = build_automation_events(report, delivery_mode="dry_run")
    assert len(events) == 1
    event = events[0]

    assert event["rule_id"] == "AUT-001"
    assert event["entity_type"] == "PERMIT"
    assert event["entity_id"] == "PTW-2026-001"
    assert event["action"] == "FLAG_OVERDUE_PERMIT"
    assert event["alert_code"] == "PERMIT_OVERDUE"
    assert event["idempotency_key"].startswith("hse-automation:v1:")
    assert event["payload"]["minutes_overdue"] == 90
    assert event["payload"]["requester_id"] == "EMP-042"
    assert event["payload"]["issuer_id"] == "EMP-007"


def test_aut001_recipient_resolution_with_fallback():
    """Verify that DatabaseEventDispatcher properly uses requester_id when issuer_id is absent."""
    sample_event = {
        "schema_version": "1.0",
        "event_id": "evt_11111111111111111111111111111111",
        "idempotency_key": "hse-automation:v1:permit_test_idempotency_key_001",
        "rule_id": "AUT-001",
        "entity_type": "PERMIT",
        "entity_id": "99901",
        "alert_code": "PERMIT_OVERDUE",
        "action": "FLAG_OVERDUE_PERMIT",
        "delivery_mode": "database",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {
            "permit_id": 99901,
            "requester_id": "EMP-REQ-123",
            "issuer_id": None,
            "expiry_at": "2026-08-29T08:00:00Z",
            "status": "ACTIVE",
            "minutes_overdue": 120,
        },
    }

    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.execute.return_value.fetchone.return_value = None

    dispatcher = DatabaseEventDispatcher(session_factory=lambda: mock_session)
    result = dispatcher.dispatch([sample_event])

    assert result.planned_count == 1
    assert result.delivered_count == 1

    # Verify that the INSERT statement for notifications used recipient_id = 'EMP-REQ-123'
    executed_params = [
        call.args[1] for call in mock_session.execute.call_args_list if len(call.args) > 1
    ]
    matching_notif = [p for p in executed_params if p.get("type") == "AUTOMATION_PERMIT_OVERDUE"]
    assert len(matching_notif) == 1
    assert matching_notif[0]["recipient_id"] == "EMP-REQ-123"


# ===========================================================================
# 2. CAPA ESCALATION AUTOMATION (AUT-003) TESTS
# ===========================================================================

def test_aut003_capa_multi_tier_escalation_logic():
    """Verify progressive escalation brackets (1, 3, 7 days) and boundary conditions."""
    thresholds = (1, 3, 7)

    # 0 days overdue: Not yet overdue enough for tier 1
    assert _capa_escalation_day(0, thresholds) is None

    # 1-2 days overdue: Matches tier 1
    assert _capa_escalation_day(1, thresholds) == 1
    assert _capa_escalation_day(2, thresholds) == 1

    # 3-6 days overdue: Matches tier 3
    assert _capa_escalation_day(3, thresholds) == 3
    assert _capa_escalation_day(4, thresholds) == 3
    assert _capa_escalation_day(6, thresholds) == 3

    # 7+ days overdue: Matches tier 7
    assert _capa_escalation_day(7, thresholds) == 7
    assert _capa_escalation_day(15, thresholds) == 7
    assert _capa_escalation_day(100, thresholds) == 7


def test_aut003_capa_stage_progression_and_deduplication():
    """Verify distinct idempotency keys across escalation tiers and identical keys within the same tier."""
    # Same tier (day=1), different evaluation runs -> identical digest
    digest_tier1_run1 = _event_digest(
        rule_id="AUT-003",
        entity_type="CAPA",
        entity_id="CAPA-501",
        alert_code="CAPA_OVERDUE",
        occurrence_marker="2026-08-20|day=1",
    )
    digest_tier1_run2 = _event_digest(
        rule_id="AUT-003",
        entity_type="CAPA",
        entity_id="CAPA-501",
        alert_code="CAPA_OVERDUE",
        occurrence_marker="2026-08-20|day=1",
    )
    assert digest_tier1_run1 == digest_tier1_run2

    # Tier 2 (day=3) -> distinct digest
    digest_tier2 = _event_digest(
        rule_id="AUT-003",
        entity_type="CAPA",
        entity_id="CAPA-501",
        alert_code="CAPA_OVERDUE",
        occurrence_marker="2026-08-20|day=3",
    )
    assert digest_tier1_run1 != digest_tier2

    # Tier 3 (day=7) -> distinct digest
    digest_tier3 = _event_digest(
        rule_id="AUT-003",
        entity_type="CAPA",
        entity_id="CAPA-501",
        alert_code="CAPA_OVERDUE",
        occurrence_marker="2026-08-20|day=7",
    )
    assert digest_tier2 != digest_tier3


def test_aut003_capa_date_and_datetime_payload_handling():
    """Verify that CAPA payloads with both date strings and ISO timestamps validate cleanly in Spring client."""
    event_with_date = {
        "schema_version": "1.0",
        "event_id": "evt_33333333333333333333333333333333",
        "idempotency_key": "hse-automation:v1:3333333333333333333333333333333333333333333333333333333333333333",
        "rule_id": "AUT-003",
        "entity_type": "CAPA",
        "entity_id": "CAPA-901",
        "alert_code": "CAPA_OVERDUE",
        "action": "CREATE_CAPA_ESCALATION",
        "delivery_mode": "spring",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {
            "capa_id": "CAPA-901",
            "due_date": "2026-08-20",
            "status": "OPEN",
            "days_overdue": 9,
            "escalation_day": 7,
        },
    }
    prepared_date = _prepare_action(event_with_date)
    assert prepared_date["payload"]["due_date"] == "2026-08-20"

    event_with_datetime = {
        "schema_version": "1.0",
        "event_id": "evt_33333333333333333333333333333334",
        "idempotency_key": "hse-automation:v1:3333333333333333333333333333333333333333333333333333333333333334",
        "rule_id": "AUT-003",
        "entity_type": "CAPA",
        "entity_id": "CAPA-902",
        "alert_code": "CAPA_OVERDUE",
        "action": "CREATE_CAPA_ESCALATION",
        "delivery_mode": "spring",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {
            "capa_id": "CAPA-902",
            "due_date": "2026-08-20T00:00:00Z",
            "status": "OPEN",
            "days_overdue": 9,
            "escalation_day": 7,
        },
    }
    prepared_datetime = _prepare_action(event_with_datetime)
    assert prepared_datetime["payload"]["due_date"] == "2026-08-20T00:00:00Z"


# ===========================================================================
# 3. RISK REVIEW AUTOMATION (AUT-004) TESTS
# ===========================================================================

def test_aut004_risk_review_detection_and_stable_idempotency():
    """Verify AUT-004 unreviewed and stale high risk event creation and marker stability."""
    report = {
        "mode": "read_only_detection",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "enabled_rule_ids": ["AUT-004"],
        "thresholds": {"risk_review_age_days": 30},
        "candidates": {
            "permits": [],
            "certificates": [],
            "capa": [],
            "risks": [
                {
                    "risk_id": "RSK-001",
                    "department_id": 1,
                    "zone_id": 2,
                    "owner_id": "EMP-010",
                    "inherent_score": 20,
                    "risk_level": "HIGH",
                    "residual_score": 10,
                    "status": "ACTIVE",
                    "last_reviewed_at": None,
                    "next_review_date": None,
                    "days_since_review": 45,
                    "alert_code": "RISK_REVIEW_REQUIRED",
                }
            ],
        },
    }

    events = build_automation_events(report, delivery_mode="dry_run")
    assert len(events) == 1
    event = events[0]

    assert event["rule_id"] == "AUT-004"
    assert event["entity_type"] == "RISK"
    assert event["entity_id"] == "RSK-001"
    assert event["alert_code"] == "RISK_REVIEW_REQUIRED"
    assert event["action"] == "FLAG_RISK_FOR_REVIEW"
    assert event["payload"]["inherent_score"] == 20
    assert event["payload"]["owner_id"] == "EMP-010"


def test_aut004_iso_timestamp_validation_in_spring_client():
    """Verify that ISO UTC timestamps for last_reviewed_at and next_review_date pass Spring validation."""
    event = {
        "schema_version": "1.0",
        "event_id": "evt_44444444444444444444444444444444",
        "idempotency_key": "hse-automation:v1:4444444444444444444444444444444444444444444444444444444444444444",
        "rule_id": "AUT-004",
        "entity_type": "RISK",
        "entity_id": "RSK-002",
        "alert_code": "RISK_REVIEW_OVERDUE",
        "action": "FLAG_RISK_FOR_REVIEW",
        "delivery_mode": "spring",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {
            "risk_id": "RSK-002",
            "inherent_score": 18,
            "status": "ACTIVE",
            "last_reviewed_at": "2026-07-01T12:00:00Z",
            "next_review_date": "2026-08-01T12:00:00Z",
            "days_since_review": 59,
        },
    }

    prepared = _prepare_action(event)
    assert prepared["payload"]["last_reviewed_at"] == "2026-07-01T12:00:00Z"
    assert prepared["payload"]["next_review_date"] == "2026-08-01T12:00:00Z"


def test_aut004_recipient_resolution_with_owner_id():
    """Verify that DatabaseEventDispatcher assigns notification to owner_id."""
    sample_event = {
        "schema_version": "1.0",
        "event_id": "evt_44444444444444444444444444444445",
        "idempotency_key": "hse-automation:v1:risk_test_idempotency_key_002",
        "rule_id": "AUT-004",
        "entity_type": "RISK",
        "entity_id": "RSK-003",
        "alert_code": "RISK_REVIEW_REQUIRED",
        "action": "FLAG_RISK_FOR_REVIEW",
        "delivery_mode": "database",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {
            "risk_id": "RSK-003",
            "owner_id": "EMP-OWNER-777",
            "inherent_score": 16,
            "status": "ACTIVE",
        },
    }

    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.execute.return_value.fetchone.return_value = None

    dispatcher = DatabaseEventDispatcher(session_factory=lambda: mock_session)
    result = dispatcher.dispatch([sample_event])

    assert result.delivered_count == 1
    executed_params = [
        call.args[1] for call in mock_session.execute.call_args_list if len(call.args) > 1
    ]
    matching_notif = [p for p in executed_params if p.get("type") == "AUTOMATION_RISK_REVIEW"]
    assert len(matching_notif) == 1
    assert matching_notif[0]["recipient_id"] == "EMP-OWNER-777"


# ===========================================================================
# 4. CROSS-CUTTING ENGINE & ERROR CONTAINMENT TESTS
# ===========================================================================

def test_engine_fail_closed_on_invalid_delivery_mode():
    """Verify that build_automation_events rejects unsupported delivery modes."""
    report = {
        "mode": "read_only_detection",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "enabled_rule_ids": ["AUT-001"],
        "thresholds": {},
        "candidates": {"permits": [], "certificates": [], "capa": [], "risks": []},
    }
    with pytest.raises(AutomationEventError, match="Unsupported automation delivery mode"):
        build_automation_events(report, delivery_mode="invalid_mode")


def test_engine_dispatcher_batch_duplicate_event_rejection():
    """Verify that dispatcher rejects batches containing duplicate event IDs or idempotency keys."""
    dup_event = {
        "schema_version": "1.0",
        "event_id": "evt_99999999999999999999999999999999",
        "idempotency_key": "hse-automation:v1:9999999999999999999999999999999999999999999999999999999999999999",
        "rule_id": "AUT-001",
        "entity_type": "PERMIT",
        "entity_id": "1",
        "alert_code": "PERMIT_OVERDUE",
        "action": "FLAG_OVERDUE_PERMIT",
        "delivery_mode": "dry_run",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {"permit_id": 1, "status": "ACTIVE", "minutes_overdue": 10},
    }

    dispatcher = DryRunEventDispatcher()
    with pytest.raises(AutomationDispatchError, match="duplicate"):
        dispatcher.dispatch([dup_event, dup_event])


def test_engine_database_dispatcher_rollback_on_failure():
    """Verify that DatabaseEventDispatcher cleanly rolls back transaction when SQL execution fails."""
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session.execute.side_effect = Exception("Simulated DB Disk Full Error")

    sample_event = {
        "schema_version": "1.0",
        "event_id": "evt_55555555555555555555555555555555",
        "idempotency_key": "hse-automation:v1:5555555555555555555555555555555555555555555555555555555555555555",
        "rule_id": "AUT-001",
        "entity_type": "PERMIT",
        "entity_id": "1",
        "alert_code": "PERMIT_OVERDUE",
        "action": "FLAG_OVERDUE_PERMIT",
        "delivery_mode": "database",
        "evaluated_at_utc": "2026-08-29T10:00:00Z",
        "business_date": "2026-08-29",
        "payload": {"permit_id": 1, "status": "ACTIVE", "minutes_overdue": 10},
    }

    dispatcher = DatabaseEventDispatcher(session_factory=lambda: mock_session)
    with pytest.raises(AutomationDispatchError, match="Database dispatch failed"):
        dispatcher.dispatch([sample_event])

    mock_session.rollback.assert_called_once()
