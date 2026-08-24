"""
Implementations for tools listed in app/tools/definitions.py.

Every function takes a SQLAlchemy Session + parameters, returning a JSON-serialisable dict:
{"rows": [...], "count": N} or relevant summary dict.
All queries are strict READ-ONLY.
"""
from datetime import datetime, date
from decimal import Decimal
import re
from sqlalchemy import text
from sqlalchemy.orm import Session


def _clean_val(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, bytes):
        return v.decode('utf-8', errors='ignore')
    return v


def _query_rows(db: Session, sql: str, params: dict | None = None) -> list[dict]:
    """Executes a parameterized read-only query and normalizes result values."""
    try:
        result = db.execute(text(sql), params or {})
        return [{key: _clean_val(value) for key, value in row.items()} for row in result.mappings()]
    except Exception:
        return []


def run_read_only_query(db: Session, sql_query: str):
    """
    Executes a read-only SQL SELECT query on MySQL.
    Supports all database tables.
    """
    clean_sql = sql_query.strip().rstrip(";")
    if not re.match(r"^(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN)\b", clean_sql, re.IGNORECASE):
        return {"error": "Only SELECT, WITH, SHOW, or DESCRIBE queries are permitted."}

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", clean_sql, re.IGNORECASE):
            return {"error": f"Forbidden keyword '{kw}' detected. Only read-only queries are permitted."}

    try:
        res = db.execute(text(clean_sql))
        if not res.returns_rows:
            return {"rows": [], "count": 0}

        result = res.fetchall()
        if not result:
            return {"rows": [], "count": 0}

        keys = res.keys()
        sensitive_cols = {"password", "password_hash", "client_secret", "secret", "token", "access_token"}
        rows = [
            {k: ("[REDACTED]" if k.lower() in sensitive_cols else _clean_val(v)) for k, v in zip(keys, row)}
            for row in result
        ]
        return {
            "total_count": len(result),
            "returned_count": min(len(rows), 30),
            "rows": rows[:30]  # Safe bounds for fast LLM context processing
        }
    except Exception as exc:
        return {"error": f"SQL execution error: {str(exc)}"}


def get_db_schema(db: Session, table_name: str | None = None):
    """
    Inspects column structure for specified table or lists all tables.
    """
    if table_name:
        clean_table = table_name.strip().replace("`", "")
        try:
            cols = db.execute(text(f"DESCRIBE `{clean_table}`")).fetchall()
            return {
                "table": clean_table,
                "columns": [{"name": c[0], "type": c[1], "null": c[2], "key": c[3]} for c in cols]
            }
        except Exception as e:
            return {"error": f"Table '{clean_table}' error: {e}"}

    tables = db.execute(text("SHOW TABLES")).fetchall()
    table_list = [r[0] for r in tables]
    return {"total_tables": len(table_list), "tables": table_list}


def list_incidents(db: Session, status: str | None = None, limit: int | None = 10, **kwargs):
    where = ""
    params = {}
    if status:
        where = "WHERE UPPER(incident_status.name) = :status"
        params["status"] = status.upper().strip()
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT incidents.incident_id, incidents.reported_at, incidents.zone_id,
               incidents.title, incidents.description, incidents.lost_days,
               incident_status.name AS status, incident_severity.name AS severity
        FROM incidents
        LEFT JOIN incident_statuses AS incident_status ON incident_status.incident_status_id = incidents.status_id
        LEFT JOIN incident_severities AS incident_severity ON incident_severity.incident_severity_id = incidents.severity_id
        {where}
        ORDER BY incidents.reported_at DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_overdue_capas(db: Session, limit: int | None = 15, **kwargs):
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT capa.capa_id, capa.title, capa.due_date, capa.days_overdue,
               capa_status.name AS status, capa_priority.name AS priority
        FROM capa
        LEFT JOIN capa_statuses AS capa_status ON capa_status.capa_status_id = capa.status_id
        LEFT JOIN capa_priorities AS capa_priority ON capa_priority.capa_priority_id = capa.priority_id
        WHERE capa.due_date < CURDATE() AND (UPPER(capa_status.name) <> 'COMPLETED' OR capa_status.name IS NULL)
        ORDER BY capa.due_date ASC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_employee_info(db: Session, employee_id: str | None = None, query: str | None = None, limit: int | None = 10, **kwargs):
    where = ""
    params: dict = {}
    if employee_id:
        raw = str(employee_id).strip().removeprefix("EMP-").lstrip("0")
        try:
            params["employee_id"] = int(raw) if raw else 0
            where = "WHERE employee_id = :employee_id"
        except ValueError:
            params["query"] = f"%{str(employee_id).strip()}%"
            where = "WHERE display_name LIKE :query OR CAST(employee_id AS CHAR) LIKE :query"
    elif query:
        where = "WHERE display_name LIKE :query OR job_title LIKE :query OR CAST(employee_id AS CHAR) LIKE :query"
        params["query"] = f"%{query}%"
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT employee_id, display_name, zone_id, job_title, manager_id,
               hire_date, email_alias, phone_ext, active_flag
        FROM employees {where} ORDER BY employee_id {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_monthly_kpis(db: Session, month: str | None = None, limit: int | None = 12, **kwargs):
    where = ""
    params = {}
    if month:
        where = "WHERE month = :month"
        params["month"] = month.strip()
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 12"
    rows = _query_rows(db, f"""
        SELECT kpi_id, month, hours_worked, recordable_incidents, lost_time_injuries,
               lost_days, near_misses, safety_observations, trir, ltifr
        FROM monthly_kpis
        {where}
        ORDER BY month DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_recent_ai_events(db: Session, severity: str | None = None, limit: int | None = 10, **kwargs):
    where = ""
    params = {}
    if severity:
        where = "WHERE UPPER(ai_event_severity.name) = :severity"
        params["severity"] = severity.upper().strip()
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT ai_events.ai_event_id, ai_events.detected_at, ai_events.event_type,
               ai_events.camera_id, ai_events.employee_id, ai_events.confidence_pct,
               ai_event_severity.name AS severity, ai_events.action_taken
        FROM ai_events
        LEFT JOIN ai_event_severities AS ai_event_severity ON ai_event_severity.ai_event_severity_id = ai_events.severity_id
        {where} ORDER BY ai_events.detected_at DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_recent_sensor_alerts(db: Session, limit: int | None = 10, **kwargs):
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT reading_id, sensor_id, captured_at, value, unit,
               safe_min, safe_max, warning_min, warning_max, alert_level
        FROM sensor_readings
        ORDER BY captured_at DESC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_chemicals(db: Session, query: str | None = None, limit: int | None = 15, **kwargs):
    where = ""
    params = {}
    if query:
        where = """WHERE trade_name LIKE :q OR chemical_name LIKE :q
                         OR ghs_classes LIKE :q OR cas_number LIKE :q"""
        params["q"] = f"%{query}%"
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT chemical_id, trade_name, chemical_name, cas_number,
               supplier, quantity, unit, ghs_classes, zone_id
        FROM chemicals
        {where}
        ORDER BY chemical_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_permits(db: Session, status: str | None = None, risk_level: str | None = None, limit: int | None = 10, **kwargs):
    filters, params = [], {}
    if status:
        filters.append("UPPER(permit_status.name) = :status")
        params["status"] = status.upper().strip()
    if risk_level:
        filters.append("UPPER(permit_risk.name) = :risk_level")
        params["risk_level"] = risk_level.upper().strip()
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT permits.permit_id, permit_type.name AS permit_type, permits.zone_id,
               permits.work_description, permits.start_at, permits.expiry_at,
               permit_risk.name AS risk_level, permit_status.name AS status
        FROM permits
        LEFT JOIN permit_types AS permit_type ON permit_type.permit_type_id = permits.permit_type_id
        LEFT JOIN permit_risk_levels AS permit_risk ON permit_risk.permit_risk_level_id = permits.risk_level_id
        LEFT JOIN permit_statuses AS permit_status ON permit_status.permit_status_id = permits.status_id
        {where} ORDER BY permits.start_at DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_inspections(db: Session, status: str | None = None, limit: int | None = 10, **kwargs):
    where = ""
    params = {}
    if status:
        where = "WHERE UPPER(inspection_status.name) = :status"
        params["status"] = status.upper().strip()
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT inspections.inspection_id, inspections.inspection_type, inspections.zone_id,
               inspections.scheduled_at, inspections.completed_at, inspections.score_pct,
               inspection_status.name AS status
        FROM inspections
        LEFT JOIN inspection_statuses AS inspection_status ON inspection_status.inspection_status_id = inspections.status_id
        {where} ORDER BY inspections.scheduled_at DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_ppe_inventory(db: Session, category: str | None = None, limit: int | None = 15, **kwargs):
    where = ""
    params = {}
    if category:
        where = "WHERE category = :category"
        params["category"] = category.strip()
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT ppe_item_id, item_code, name_ar, category, unit,
               balance_qty, reorder_threshold, monthly_consumption, supplier
        FROM ppe_inventory
        {where}
        ORDER BY ppe_item_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_risk_register(db: Session, limit: int | None = 15, **kwargs):
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT risk_id, zone_id, hazard, activity, likelihood, severity,
               inherent_score, risk_level, controls, residual_score,
               last_reviewed_at, next_review_date
        FROM risk_register
        ORDER BY inherent_score DESC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_overdue_training(db: Session, limit: int | None = 15, **kwargs):
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT cert.certificate_id, cert.employee_id, emp.display_name AS employee_name,
               course.name_ar AS course_name, cert.issue_date, cert.expiry_date,
               cert.days_to_expiry
        FROM certificates cert
        LEFT JOIN employees emp ON emp.employee_id = cert.employee_id
        LEFT JOIN training_courses course ON course.course_id = cert.course_id
        WHERE cert.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ORDER BY cert.expiry_date ASC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_fire_equipment(db: Session, limit: int | None = 15, **kwargs):
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT fe.equipment_id, fe.asset_type, fe.subtype, fe.zone_id, fe.location_detail,
               fe.capacity, fe.installation_date, fe.last_inspection_date, fe.next_inspection_date,
               fe.expiry_date, fe.vendor, fe.qr_code,
               COALESCE(fe_status.name, 'VALID') AS status
        FROM fire_equipment fe
        LEFT JOIN fire_equipment_statuses fe_status ON fe_status.fire_equipment_status_id = fe.status_id
        ORDER BY fe.installation_date DESC, fe.equipment_id DESC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_ppe_stock_status(db: Session, below_threshold_only: bool = False, limit: int | None = 15, **kwargs):
    where = "WHERE balance_qty < reorder_threshold" if below_threshold_only else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT ppe_item_id, item_code, name_ar, unit, balance_qty,
               reorder_threshold, monthly_consumption, supplier, storage_zone_id,
               CASE WHEN balance_qty < reorder_threshold THEN 1 ELSE 0 END AS is_below_threshold,
               CASE WHEN monthly_consumption > 0 THEN ROUND(balance_qty / (monthly_consumption / 30.0), 1) ELSE NULL END AS days_until_stockout
        FROM ppe_inventory
        {where}
        ORDER BY is_below_threshold DESC, balance_qty ASC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_expired_fire_equipment(db: Session, limit: int | None = 15, **kwargs):
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT fe.equipment_id, fe.asset_type, fe.subtype, fe.zone_id, fe.location_detail,
               fe.capacity, fe.expiry_date, fe.vendor, fe.next_inspection_date,
               COALESCE(fe_status.name, 'EXPIRED') AS status
        FROM fire_equipment fe
        LEFT JOIN fire_equipment_statuses fe_status ON fe_status.fire_equipment_status_id = fe.status_id
        WHERE fe_status.name = 'EXPIRED' OR fe.expiry_date <= CURDATE()
        ORDER BY fe.expiry_date ASC {limit_clause}
    """, {})
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_fire_inspections(db: Session, equipment_id: str | int | None = None, status: str | None = None, limit: int | None = 15, **kwargs):
    filters, params = [], {}
    if equipment_id:
        filters.append("fi.equipment_id = :eq_id")
        params["eq_id"] = int(equipment_id) if str(equipment_id).isdigit() else equipment_id
    if status:
        filters.append("UPPER(fir.name) = :status")
        params["status"] = status.upper().strip()
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT fi.fire_inspection_id AS id, fi.equipment_id, fi.inspected_at,
               fi.inspector_id, COALESCE(emp.display_name, 'Inspector') AS inspector_name,
               COALESCE(fir.name, 'PASSED') AS status,
               fi.action_required, fi.next_due_date, fi.work_order_id
        FROM fire_inspections fi
        LEFT JOIN fire_inspection_results fir ON fir.fire_inspection_result_id = fi.result_id
        LEFT JOIN employees emp ON emp.employee_id = fi.inspector_id
        {where}
        ORDER BY fi.inspected_at DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_fixed_safety_assets(db: Session, zone_id: str | int | None = None, limit: int | None = 15, **kwargs):
    where = ""
    params = {}
    if zone_id:
        where = "WHERE fsa.zone_id = :zone_id"
        params["zone_id"] = int(zone_id) if str(zone_id).isdigit() else zone_id
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT fsa.asset_summary_id AS id, fsa.asset_name, fsa.asset_type,
               fsa.total_qty, fsa.operational_qty, fsa.last_test_date, fsa.next_test_date,
               COALESCE(fsas.name, 'OPERATIONAL') AS status, fsa.notes
        FROM fixed_safety_assets fsa
        LEFT JOIN fixed_safety_asset_statuses fsas ON fsas.fixed_safety_asset_status_id = fsa.status_id
        {where}
        ORDER BY fsa.asset_summary_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


# Dispatch dictionary
HANDLERS = {
    "run_read_only_query": run_read_only_query,
    "get_db_schema": get_db_schema,
    "list_incidents": list_incidents,
    "list_overdue_capas": list_overdue_capas,
    "get_employee_info": get_employee_info,
    "get_monthly_kpis": get_monthly_kpis,
    "get_recent_ai_events": get_recent_ai_events,
    "get_recent_sensor_alerts": get_recent_sensor_alerts,
    "list_chemicals": list_chemicals,
    "list_permits": list_permits,
    "list_inspections": list_inspections,
    "list_ppe_inventory": list_ppe_inventory,
    "list_risk_register": list_risk_register,
    "get_overdue_training": get_overdue_training,
    "list_fire_equipment": list_fire_equipment,
    "get_ppe_stock_status": get_ppe_stock_status,
    "get_expired_fire_equipment": get_expired_fire_equipment,
    "list_fire_inspections": list_fire_inspections,
    "list_fixed_safety_assets": list_fixed_safety_assets,
}
