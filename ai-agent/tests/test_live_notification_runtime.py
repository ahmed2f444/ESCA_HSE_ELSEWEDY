"""Unit tests for the explicit live-notification runtime gates."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import SecretStr
import pytest

from app.automation.dispatcher import (
    AutomationDispatchError,
    DatabaseEventDispatcher,
    DryRunEventDispatcher,
    SpringEventDispatcher,
    create_event_dispatcher,
)
from app.automation.runtime import create_scheduler_controller
from app.automation.spring_client import SpringClientConfig
from app.config import Settings


def configured_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "automation_delivery_mode": "dry_run",
        "automation_live_enabled": False,
        "spring_api_base_url": "http://localhost:8080",
        "automation_client_id": "test-automation-client",
        "automation_client_secret": SecretStr("test-automation-secret"),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_dry_run_requires_both_live_gates_to_be_off() -> None:
    dispatcher = create_event_dispatcher(configured_settings())
    assert isinstance(dispatcher, DryRunEventDispatcher)
    dispatcher.close()


@pytest.mark.parametrize(
    ("mode", "live_enabled"),
    [("dry_run", True), ("spring", False), ("database", False)],
)
def test_contradictory_live_settings_fail_closed(
    mode: str,
    live_enabled: bool,
) -> None:
    with pytest.raises(AutomationDispatchError):
        create_event_dispatcher(
            configured_settings(
                automation_delivery_mode=mode,
                automation_live_enabled=live_enabled,
            )
        )


def test_live_settings_create_spring_dispatcher_without_network() -> None:
    dispatcher = create_event_dispatcher(
        configured_settings(
            automation_delivery_mode="spring",
            automation_live_enabled=True,
        )
    )
    assert isinstance(dispatcher, SpringEventDispatcher)
    dispatcher.close()


def test_live_settings_create_database_dispatcher() -> None:
    dispatcher = create_event_dispatcher(
        configured_settings(
            automation_delivery_mode="database",
            automation_live_enabled=True,
        )
    )
    assert isinstance(dispatcher, DatabaseEventDispatcher)
    dispatcher.close()


def test_private_compose_backend_alias_is_accepted() -> None:
    config = SpringClientConfig(
        base_url="http://backend:8080",
        client_id="test-automation-client",
        client_secret=SecretStr("test-automation-secret"),
    )
    assert config.base_url == "http://backend:8080"


def test_runtime_plans_spring_events_for_spring_dispatcher() -> None:
    controller = create_scheduler_controller(
        BackgroundScheduler(),
        configured_settings(
            automation_delivery_mode="spring",
            automation_live_enabled=True,
        ),
    )
    try:
        assert controller.delivery_mode == "spring"
        report = {
            "mode": "read_only_detection",
            "evaluated_at_utc": "2026-08-27T09:00:00Z",
            "business_date": "2026-08-27",
            "enabled_rule_ids": ["AUT-001"],
            "thresholds": {},
            "candidates": {
                "permits": [
                    {
                        "permit_id": "PTW-LIVE-001",
                        "alert_code": "PERMIT_OVERDUE",
                        "expiry_at": "2026-08-27T08:00:00Z",
                        "status": "ACTIVE",
                        "minutes_overdue": 60,
                    }
                ],
                "certificates": [],
                "capa": [],
                "risks": [],
            },
        }
        events = controller._event_builder(report)
        assert len(events) == 1
        assert events[0]["delivery_mode"] == "spring"
        assert events[0]["rule_id"] == "AUT-001"
        assert events[0]["entity_id"] == "PTW-LIVE-001"
    finally:
        controller.close()


def test_live_notifications_api_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/notifications?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "id" in item
        assert "title" in item
        assert "unread" in item
        assert "to" in item


def test_automation_trigger_api_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/v1/automation/trigger")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert "summary" in data

