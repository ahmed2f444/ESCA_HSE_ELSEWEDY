#!/usr/bin/env python3
"""Read-only MySQL integration validation for the ESCA HSE agents."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import SessionLocal, engine
from app.main import app
from app.tools.handlers import HANDLERS, run_read_only_query


def compact_result(result: object) -> dict:
    if isinstance(result, dict):
        return {
            "passed": "error" not in result,
            "count": result.get("count", result.get("total_tables")),
            "source": result.get("source", "mysql"),
            "error": result.get("error"),
        }
    return {"passed": True, "value": result}


def validate_database_handlers() -> dict:
    db = SessionLocal()
    checks = {
        "get_db_schema": lambda: HANDLERS["get_db_schema"](db),
        "list_incidents": lambda: HANDLERS["list_incidents"](db),
        "list_overdue_capas": lambda: HANDLERS["list_overdue_capas"](db),
        "get_employee_info": lambda: HANDLERS["get_employee_info"](db),
        "get_monthly_kpis": lambda: HANDLERS["get_monthly_kpis"](db),
        "get_recent_ai_events": lambda: HANDLERS["get_recent_ai_events"](db),
        "get_recent_sensor_alerts": lambda: HANDLERS["get_recent_sensor_alerts"](db),
        "list_chemicals": lambda: HANDLERS["list_chemicals"](db),
        "list_permits": lambda: HANDLERS["list_permits"](db),
        "list_inspections": lambda: HANDLERS["list_inspections"](db),
        "list_ppe_inventory": lambda: HANDLERS["list_ppe_inventory"](db),
        "list_risk_register": lambda: HANDLERS["list_risk_register"](db),
    }
    outcomes = {}
    try:
        with engine.connect() as connection:
            outcomes["connection"] = {
                "passed": connection.execute(text("SELECT 1")).scalar_one() == 1,
                "schema": connection.execute(text("SELECT DATABASE()")).scalar_one(),
            }
        for name, check in checks.items():
            try:
                outcomes[name] = compact_result(check())
            except Exception as exc:  # Records integration failures instead of aborting.
                outcomes[name] = {"passed": False, "error": str(exc)}
        outcomes["mutation_guards"] = {
            query: run_read_only_query(db, query).get("error")
            for query in (
                "UPDATE chemicals SET chemical_name = 'blocked'",
                "DELETE FROM chemicals",
                "DROP TABLE chemicals",
            )
        }
    finally:
        db.close()
    return outcomes


def validate_api(model_mode: str, question: str) -> dict:
    client = TestClient(app)
    health = client.get("/health")
    response = client.post(
        "/api/ask",
        json={
            "question": question,
            "model_mode": model_mode,
            "session_id": f"mysql-validation-{model_mode}",
        },
    )
    body = response.json()
    return {
        "health_status": health.status_code,
        "ask_status": response.status_code,
        "model_used": body.get("model_used"),
        "tool_calls": body.get("tool_calls"),
        "answer": body.get("answer"),
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(validate_database_handlers(), indent=2, default=str))
    if len(sys.argv) > 1:
        print(json.dumps(validate_api(sys.argv[1], sys.argv[2]), indent=2, default=str))
