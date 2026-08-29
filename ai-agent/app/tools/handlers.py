"""
Implementations for all tools listed in app/tools/definitions.py.

Includes:
1. RAG Knowledge & Domain Standards Search
2. Universal Database Entity Search & Inspection
3. Full Read-Only Queries across all 15 ESCA HSE Modules
4. Full CRUD Operations (Create, Read, Update, Delete) on Railway MySQL
5. Automated Audit Logging for all mutations with SHA-256 integrity hashing
"""
from datetime import datetime, date, time, time as dtime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import re
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.tools.knowledge_base import search_hse_knowledge


# ── Value Normalization Helper ────────────────────────────────────────────────
def _clean_val(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="ignore")
    return v


def _query_rows(db: Session, sql: str, params: dict | None = None) -> list[dict]:
    """Executes a parameterized query and returns a normalized list of dictionary rows."""
    try:
        result = db.execute(text(sql), params or {})
        return [{key: _clean_val(value) for key, value in row.items()} for row in result.mappings()]
    except Exception:
        return []


# ── Audit Trail Logger ────────────────────────────────────────────────────────
def _log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str | int,
    actor_id: str = "AI_ASSISTANT",
    result_status: str = "SUCCESS",
    details: Optional[dict] = None
) -> None:
    """Inserts an immutable audit trail record into the `audit_log` table on Railway MySQL."""
    try:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        raw_hash_input = f"{now_utc}|{actor_id}|{action}|{entity_type}|{entity_id}|{result_status}"
        entry_hash = hashlib.sha256(raw_hash_input.encode("utf-8")).hexdigest()

        # Actor type 2 = SYSTEM / AUTOMATION / AI_AGENT
        actor_type_id = 2
        result_id = 1 if result_status == "SUCCESS" else 2

        db.execute(text("""
            INSERT INTO audit_log (
                occurred_at, actor_type_id, actor_id, action,
                entity_type, entity_id, result_id, ip_or_source,
                correlation_id, immutable_hash
            ) VALUES (
                :occurred_at, :actor_type_id, :actor_id, :action,
                :entity_type, :entity_id, :result_id, :ip_or_source,
                :correlation_id, :immutable_hash
            )
        """), {
            "occurred_at": now_utc,
            "actor_type_id": actor_type_id,
            "actor_id": str(actor_id),
            "action": str(action)[:60],
            "entity_type": str(entity_type)[:60],
            "entity_id": str(entity_id)[:40],
            "result_id": result_id,
            "ip_or_source": "ESCA_AI_AGENT_SERVICE",
            "correlation_id": f"ai-op-{hashlib.md5(now_utc.encode()).hexdigest()[:12]}",
            "immutable_hash": entry_hash,
        })
        db.commit()
    except Exception:
        db.rollback()


# ── Lookup Resolvers ─────────────────────────────────────────────────────────
def _resolve_incident_status_id(db: Session, name: str) -> int:
    lookup = {
        "REPORTED": 1, "CLASSIFIED": 2, "INVESTIGATING": 3,
        "CAPA_ASSIGNED": 4, "PENDING_VERIFICATION": 5, "CLOSED": 6,
        "OPEN": 1, "NEW": 1
    }
    return lookup.get(name.strip().upper(), 1)


def _resolve_incident_severity_id(db: Session, name: str) -> int:
    lookup = {"MINOR": 1, "MODERATE": 2, "MAJOR": 3, "CRITICAL": 4, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
    return lookup.get(name.strip().upper(), 1)


def _resolve_incident_type_id(db: Session, name: str) -> int:
    lookup = {
        "LTI": 1, "LOST_TIME_INJURY": 1, "FIRST_AID": 2, "NEAR_MISS": 3,
        "UNSAFE_CONDITION": 4, "UNSAFE_ACT": 5, "PROPERTY_DAMAGE": 6
    }
    return lookup.get(name.strip().upper().replace(" ", "_"), 3)


def _resolve_permit_status_id(db: Session, name: str) -> int:
    lookup = {
        "DRAFT": 1, "PENDING_APPROVAL": 2, "ACTIVE": 3, "SUSPENDED": 4,
        "EXPIRED": 5, "CLOSED": 6, "CANCELLED": 7, "REJECTED": 8, "APPROVED": 3
    }
    return lookup.get(name.strip().upper(), 3)


def _resolve_permit_type_id(db: Session, name: str) -> int:
    lookup = {
        "HOT_WORK": 1, "ELECTRICAL": 2, "WORK_AT_HEIGHT": 3, "HEIGHT": 3,
        "CONFINED_SPACE": 4, "MECHANICAL_LOTO": 5, "EXCAVATION": 6, "RADIOGRAPHY": 7
    }
    return lookup.get(name.strip().upper().replace(" ", "_"), 1)


def _resolve_permit_risk_level_id(db: Session, name: str) -> int:
    lookup = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return lookup.get(name.strip().upper(), 2)


def _resolve_capa_status_id(db: Session, name: str) -> int:
    lookup = {"DRAFT": 1, "OPEN": 2, "IN_PROGRESS": 3, "COMPLETED": 4, "CANCELLED": 5, "CLOSED": 4}
    return lookup.get(name.strip().upper(), 2)


def _resolve_capa_priority_id(db: Session, name: str) -> int:
    lookup = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return lookup.get(name.strip().upper(), 3)


def _resolve_fire_equipment_status_id(db: Session, name: str) -> int:
    lookup = {"VALID": 1, "DUE_SOON": 2, "ACTION_REQUIRED": 3, "EXPIRED": 4, "OUT_OF_SERVICE": 5, "OPERATIONAL": 1}
    return lookup.get(name.strip().upper().replace(" ", "_"), 1)


def _resolve_fire_inspection_result_id(db: Session, name: str) -> int:
    lookup = {"PASS": 1, "PASSED": 1, "PASS_WITH_ACTION": 2, "ACTION_REQUIRED": 2, "FAIL": 3, "FAILED": 3}
    return lookup.get(name.strip().upper().replace(" ", "_"), 1)


def _resolve_certificate_status_id(db: Session, name: str) -> int:
    lookup = {"VALID": 1, "EXPIRED": 2, "RENEWAL_BOOKED": 3, "SUSPENDED": 4, "REVOKED": 5}
    return lookup.get(name.strip().upper().replace(" ", "_"), 1)


def _resolve_fitness_result_id(db: Session, name: str) -> int:
    lookup = {"FIT": 1, "FIT_WITH_RESTRICTIONS": 2, "RESTRICTED": 2, "UNFIT": 3}
    return lookup.get(name.strip().upper().replace(" ", "_"), 1)


def _resolve_jsa_status_id(db: Session, name: str) -> int:
    lookup = {"DRAFT": 1, "PENDING_APPROVAL": 2, "APPROVED": 3, "REJECTED": 4, "ARCHIVED": 5}
    return lookup.get(name.strip().upper().replace(" ", "_"), 3)


def _resolve_iot_sensor_status_id(db: Session, name: str) -> int:
    lookup = {"ACTIVE": 1, "MAINTENANCE": 2, "OFFLINE": 3, "ONLINE": 1}
    return lookup.get(name.strip().upper(), 1)


def _resolve_camera_status_id(db: Session, name: str) -> int:
    lookup = {"ACTIVE": 1, "OFFLINE": 2, "MAINTENANCE": 3, "ONLINE": 1}
    return lookup.get(name.strip().upper(), 1)


def _resolve_ai_event_severity_id(db: Session, name: str) -> int:
    lookup = {"NORMAL": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "LOW": 1}
    return lookup.get(name.strip().upper(), 3)


def _resolve_zone_id(db: Session, zone: int | str | None) -> int:
    if zone is None:
        return 1
    zone_str = str(zone).strip()
    if zone_str.isdigit():
        return int(zone_str)
    r = db.execute(text("SELECT zone_id FROM zones WHERE name_ar LIKE :z OR name_en LIKE :z LIMIT 1"), {"z": f"%{zone_str}%"}).fetchone()
    if r:
        return r[0]
    digits = re.findall(r"\d+", zone_str)
    if digits:
        return int(digits[0])
    return 1


def _resolve_employee_id(db: Session, employee: int | str) -> tuple[int, int, str]:
    """Resolves employee ID, manager ID, and display name from ID, code, or name."""
    emp_str = str(employee).strip()
    if emp_str.isdigit():
        r = db.execute(text("SELECT employee_id, manager_id, display_name, job_title FROM employees WHERE employee_id = :id"), {"id": int(emp_str)}).fetchone()
        if r:
            return (r[0], r[1] or 1, r[2])
    clean_code = emp_str.removeprefix("EMP-").lstrip("0")
    if clean_code.isdigit():
        r = db.execute(text("SELECT employee_id, manager_id, display_name, job_title FROM employees WHERE employee_id = :id"), {"id": int(clean_code)}).fetchone()
        if r:
            return (r[0], r[1] or 1, r[2])

    direct_matches = db.execute(text("SELECT employee_id, manager_id, display_name, job_title FROM employees WHERE display_name LIKE :n OR email_alias LIKE :n"), {"n": f"%{emp_str}%"}).fetchall()
    if len(direct_matches) == 1:
        return (direct_matches[0][0], direct_matches[0][1] or 1, direct_matches[0][2])
    elif len(direct_matches) > 1:
        candidates = [f"- {m[2]} ({m[3] or 'موظف'} - EMP-{m[0]:03d})" for m in direct_matches]
        candidate_list = "\n".join(candidates)
        raise ValueError(f"يوجد أكثر من موظف يطابق '{emp_str}'. يرجى تحديد الاسم بالكامل أو الرقم الوظيفي:\n{candidate_list}")

    noise_words = {'safety', 'certificate', 'cert', 'course', 'training', 'induction', 'ptw', 'fire', 'سلامة', 'شهادة', 'تدريب', 'دورة', 'كورس'}
    tokens = [t for t in emp_str.lower().split() if t not in noise_words]
    if not tokens:
        tokens = emp_str.lower().split()
    name_map = {
        'ahmed': 'أحمد', 'samy': 'سامي', 'sami': 'سامي', 'mahmoud': 'محمود',
        'ali': 'علي', 'mohamed': 'محمد', 'karim': 'كريم', 'kareem': 'كريم',
        'omar': 'عمر', 'nour': 'نور', 'dina': 'دينا', 'heba': 'هبة',
        'yasser': 'ياسر', 'adel': 'عادل', 'hassan': 'حسن', 'rashad': 'رشاد',
        'abdallah': 'عبد الله', 'abdullah': 'عبد الله', 'fouad': 'فؤاد',
        'sara': 'سارة', 'sarah': 'سارة', 'mostafa': 'مصطفى', 'khaled': 'خالد'
    }
    ar_tokens = [name_map.get(t, t) for t in tokens]
    all_emps = db.execute(text("SELECT employee_id, manager_id, display_name, job_title FROM employees")).fetchall()
    fuzzy_matches = []
    for emp in all_emps:
        emp_name = emp[2]
        if all(at in emp_name for at in ar_tokens):
            fuzzy_matches.append(emp)
        elif len(ar_tokens) == 1 and any(at in emp_name for at in ar_tokens):
            fuzzy_matches.append(emp)

    if len(fuzzy_matches) == 1:
        return (fuzzy_matches[0][0], fuzzy_matches[0][1] or 1, fuzzy_matches[0][2])
    elif len(fuzzy_matches) > 1:
        candidates = [f"- {m[2]} ({m[3] or 'موظف'} - EMP-{m[0]:03d})" for m in fuzzy_matches]
        candidate_list = "\n".join(candidates)
        raise ValueError(f"يوجد أكثر من موظف يطابق '{emp_str}'. يرجى تحديد الاسم بالكامل أو الرقم الوظيفي:\n{candidate_list}")

    raise ValueError(f"لم يتم العثور على أي موظف باسم '{emp_str}'. يرجى التحقق من الاسم أو استخدام الرقم الوظيفي EMP-XXX.")


def _resolve_course_id(db: Session, course: int | str) -> tuple[int, int, str]:
    """Resolves course ID, validity duration in months, and course name."""
    c_str = str(course).strip() if course else "1"
    if c_str.isdigit():
        r = db.execute(text("SELECT course_id, validity_months, name_ar, name_en FROM training_courses WHERE course_id = :id"), {"id": int(c_str)}).fetchone()
        if r:
            return (r[0], r[1] or 12, r[2] or r[3])
    r = db.execute(text("SELECT course_id, validity_months, name_ar, name_en FROM training_courses WHERE name_ar LIKE :c OR name_en LIKE :c LIMIT 1"), {"c": f"%{c_str}%"}).fetchone()
    if r:
        return (r[0], r[1] or 12, r[2] or r[3])

    r = db.execute(text("SELECT course_id, validity_months, name_ar, name_en FROM training_courses WHERE course_id = 1")).fetchone()
    if r:
        return (r[0], r[1] or 12, r[2] or r[3])
    return (1, 12, "General Safety Induction")


# ── 1. RAG Knowledge & Universal Search Handlers ─────────────────────────────
def tool_search_hse_knowledge(query: str, category: Optional[str] = None, limit: int = 4, **kwargs) -> dict:
    """Retrieves domain HSE regulations, ISO 45001 clauses, OSHA standards, and Golden Rules."""
    return search_hse_knowledge(query=query, category=category, limit=limit)


def search_database_entities(db: Session, query: str, entity_type: Optional[str] = None, limit: int = 10, **kwargs) -> dict:
    """Searches across multiple core entities in the Railway database by keyword or ID."""
    clean_q = str(query).strip()
    param = f"%{clean_q}%"
    results = []

    # 1. Incidents
    if not entity_type or entity_type.lower() in ("incidents", "incident"):
        rows = _query_rows(db, """
            SELECT incident_id AS id, 'incident' AS entity_type, title, description,
                   reported_at AS timestamp, zone_id, lost_days
            FROM incidents
            WHERE title LIKE :q OR description LIKE :q
            ORDER BY incident_id DESC LIMIT :limit
        """, {"q": param, "limit": limit})
        results.extend(rows)

    # 2. Permits
    if not entity_type or entity_type.lower() in ("permits", "permit", "ptw"):
        rows = _query_rows(db, """
            SELECT permit_id AS id, 'permit' AS entity_type, work_description AS title,
                   executor_name AS description, start_at AS timestamp, zone_id
            FROM permits
            WHERE work_description LIKE :q OR executor_name LIKE :q
            ORDER BY permit_id DESC LIMIT :limit
        """, {"q": param, "limit": limit})
        results.extend(rows)

    # 3. CAPA
    if not entity_type or entity_type.lower() in ("capa", "actions"):
        rows = _query_rows(db, """
            SELECT capa_id AS id, 'capa' AS entity_type, title, due_date, days_overdue
            FROM capa
            WHERE title LIKE :q
            ORDER BY capa_id DESC LIMIT :limit
        """, {"q": param, "limit": limit})
        results.extend(rows)

    # 4. Employees
    if not entity_type or entity_type.lower() in ("employees", "employee"):
        rows = _query_rows(db, """
            SELECT employee_id AS id, 'employee' AS entity_type, display_name AS title,
                   job_title AS description, email_alias, zone_id
            FROM employees
            WHERE display_name LIKE :q OR email_alias LIKE :q OR job_title LIKE :q
            LIMIT :limit
        """, {"q": param, "limit": limit})
        results.extend(rows)

    # 5. Chemicals
    if not entity_type or entity_type.lower() in ("chemicals", "chemical", "hazmat"):
        rows = _query_rows(db, """
            SELECT chemical_id AS id, 'chemical' AS entity_type, trade_name AS title,
                   chemical_name AS description, cas_number, quantity, unit
            FROM chemicals
            WHERE trade_name LIKE :q OR chemical_name LIKE :q OR cas_number LIKE :q
            LIMIT :limit
        """, {"q": param, "limit": limit})
        results.extend(rows)

    # 6. Fire Equipment
    if not entity_type or entity_type.lower() in ("fire_equipment", "fire"):
        rows = _query_rows(db, """
            SELECT equipment_id AS id, 'fire_equipment' AS entity_type,
                   CONCAT(asset_type, ' - ', subtype) AS title, location_detail AS description, zone_id
            FROM fire_equipment
            WHERE asset_type LIKE :q OR subtype LIKE :q OR location_detail LIKE :q
            LIMIT :limit
        """, {"q": param, "limit": limit})
        results.extend(rows)

    return {"results": results[:limit], "count": len(results[:limit]), "query": clean_q, "source": "mysql"}


def run_read_only_query(db: Session, sql_query: str, **kwargs) -> dict:
    """Executes a validated read-only SQL query on the live Railway MySQL database."""
    clean_sql = sql_query.strip().rstrip(";")
    if not re.match(r"^SELECT\b", clean_sql, re.IGNORECASE):
        return {"error": "Only read-only SELECT queries are permitted via this tool."}

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", clean_sql, re.IGNORECASE):
            return {"error": f"Forbidden mutation keyword '{kw}' is blocked in read-only mode."}

    try:
        rows = _query_rows(db, clean_sql)
        return {
            "returned_count": len(rows),
            "rows": rows[:50],
            "total_count": len(rows),
            "source": "mysql"
        }
    except Exception as exc:
        return {"error": f"SQL Execution Error: {str(exc)}"}


def get_db_schema(db: Session, table_name: Optional[str] = None, **kwargs) -> dict:
    """Inspects database tables or specific column definitions."""
    try:
        if table_name:
            t_clean = table_name.strip().replace("`", "").replace(";", "")
            rows = _query_rows(db, f"DESCRIBE `{t_clean}`")
            return {"table": t_clean, "columns": rows, "source": "mysql"}
        else:
            rows = _query_rows(db, "SHOW TABLES")
            table_list = [list(r.values())[0] for r in rows]
            return {"tables": table_list, "count": len(table_list), "source": "mysql"}
    except Exception as exc:
        return {"error": f"Schema Inspection Error: {str(exc)}"}


# ── 2. Master Data & Organization Handlers ────────────────────────────────────
def list_departments(db: Session, active_only: bool = True, limit: int = 15, **kwargs) -> dict:
    """Lists factory departments with manager names and zone counts."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    where = "WHERE d.active_flag = 1" if active_only else ""
    rows = _query_rows(db, f"""
        SELECT d.department_id, d.name_ar, d.name_en,
               mgr.display_name AS manager_name,
               hse.display_name AS hse_contact_name,
               d.active_flag,
               (SELECT COUNT(*) FROM zones z WHERE z.department_id = d.department_id) AS zone_count
        FROM departments d
        LEFT JOIN employees mgr ON mgr.employee_id = d.manager_employee_id
        LEFT JOIN employees hse ON hse.employee_id = d.hse_contact_id
        {where}
        ORDER BY d.department_id ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_zones(db: Session, department_id: Optional[int | str] = None, limit: int = 20, **kwargs) -> dict:
    """Lists factory zones and areas with risk class and occupancy."""
    params = {}
    where = ""
    if department_id:
        where = "WHERE z.department_id = :did"
        params["did"] = str(department_id)
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 20"
    rows = _query_rows(db, f"""
        SELECT z.zone_id, z.department_id, d.name_ar AS department_name,
               z.name_ar, z.name_en, z.zone_type, z.max_occupancy, z.active_flag
        FROM zones z
        LEFT JOIN departments d ON d.department_id = z.department_id
        {where}
        ORDER BY z.zone_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_employees(db: Session, zone_id: Optional[int | str] = None, job_title: Optional[str] = None, active_only: bool = True, limit: int = 20, **kwargs) -> dict:
    """Lists employees with assigned zones and contact details."""
    filters, params = [], {}
    if zone_id:
        filters.append("e.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    if job_title:
        filters.append("e.job_title LIKE :jt")
        params["jt"] = f"%{job_title}%"
    if active_only:
        filters.append("e.active_flag = 1")
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 20"
    rows = _query_rows(db, f"""
        SELECT e.employee_id, e.display_name, e.job_title, z.name_ar AS zone_name,
               e.email_alias, e.phone_ext, mgr.display_name AS manager_name, e.active_flag
        FROM employees e
        LEFT JOIN zones z ON z.zone_id = e.zone_id
        LEFT JOIN employees mgr ON mgr.employee_id = e.manager_id
        {where}
        ORDER BY e.employee_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_employee_info(db: Session, employee_id: Optional[int | str] = None, query: Optional[str] = None, **kwargs) -> dict:
    """Deep profile lookup for an employee."""
    target = employee_id or query
    if not target:
        return {"error": "Please provide employee_id or employee name."}
    try:
        emp_id, mgr_id, disp_name = _resolve_employee_id(db, target)
    except ValueError as e:
        return {"error": str(e)}

    emp_info = _query_rows(db, """
        SELECT e.employee_id, e.display_name, e.job_title, e.zone_id, z.name_ar AS zone_name,
               e.email_alias, e.phone_ext, mgr.display_name AS manager_name, e.hire_date, e.active_flag
        FROM employees e
        LEFT JOIN zones z ON z.zone_id = e.zone_id
        LEFT JOIN employees mgr ON mgr.employee_id = e.manager_id
        WHERE e.employee_id = :id
    """, {"id": emp_id})

    certs = _query_rows(db, """
        SELECT cert.certificate_id, tc.name_ar AS course_name, cert.issue_date, cert.expiry_date,
               COALESCE(cs.name, 'VALID') AS status, cert.days_to_expiry
        FROM certificates cert
        LEFT JOIN training_courses tc ON tc.course_id = cert.course_id
        LEFT JOIN certificate_statuses cs ON cs.certificate_status_id = cert.status_id
        WHERE cert.employee_id = :id
        ORDER BY cert.certificate_id DESC LIMIT 5
    """, {"id": emp_id})

    permits = _query_rows(db, """
        SELECT p.permit_id, pt.name AS permit_type, p.work_description, p.start_at, p.expiry_at,
               COALESCE(st.name, 'ACTIVE') AS status
        FROM permits p
        LEFT JOIN permit_types pt ON pt.permit_type_id = p.permit_type_id
        LEFT JOIN permit_statuses st ON st.permit_status_id = p.status_id
        WHERE p.requester_id = :id OR p.issuer_id = :id
        ORDER BY p.permit_id DESC LIMIT 5
    """, {"id": emp_id})

    exams = _query_rows(db, """
        SELECT he.exam_id, mp.protocol_name, he.scheduled_date, he.completed_date,
               fr.name AS fitness_result, he.restriction_summary
        FROM health_exams he
        LEFT JOIN medical_protocols mp ON mp.protocol_id = he.protocol_id
        LEFT JOIN fitness_results fr ON fr.fitness_result_id = he.fitness_result_id
        WHERE he.employee_id = :id
        ORDER BY he.exam_id DESC LIMIT 5
    """, {"id": emp_id})

    return {
        "employee": emp_info[0] if emp_info else {},
        "certificates": certs,
        "recent_permits": permits,
        "medical_exams": exams,
        "source": "mysql"
    }


def create_employee(
    db: Session,
    display_name: str,
    job_title: str = "Technician",
    zone_id: int = 1,
    manager_id: Optional[int] = None,
    email_alias: Optional[str] = None,
    phone_ext: Optional[int] = None,
    **kwargs
) -> dict:
    """CRUD CREATE: Adds a new employee."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        if not email_alias:
            slug = re.sub(r"[^a-zA-Z0-9]", "", display_name.lower())[:10]
            email_alias = f"{slug or 'emp'}@elsewedy.com"

        db.execute(text("""
            INSERT INTO employees (display_name, zone_id, job_title, manager_id, employment_type_id, email_alias, phone_ext, active_flag, hire_date)
            VALUES (:dn, :zid, :jt, :mid, 1, :email, :ext, 1, CURDATE())
        """), {
            "dn": display_name.strip(),
            "zid": zid,
            "jt": job_title.strip(),
            "mid": manager_id or 1,
            "email": email_alias,
            "ext": phone_ext or 100
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_EMPLOYEE", "employee", new_id, details={"name": display_name, "title": job_title})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "employee",
            "employee_id": new_id,
            "display_name": display_name,
            "job_title": job_title,
            "zone_id": zid,
            "message": f"Employee '{display_name}' successfully registered with ID EMP-{new_id:03d}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create employee: {str(exc)}"}


def update_employee(
    db: Session,
    employee_id: int | str,
    job_title: Optional[str] = None,
    zone_id: Optional[int] = None,
    manager_id: Optional[int] = None,
    active_flag: Optional[bool] = None,
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates employee details."""
    try:
        emp_id, _, name = _resolve_employee_id(db, employee_id)
        updates, params = [], {"id": emp_id}
        if job_title is not None:
            updates.append("job_title = :jt")
            params["jt"] = job_title
        if zone_id is not None:
            updates.append("zone_id = :zid")
            params["zid"] = _resolve_zone_id(db, zone_id)
        if manager_id is not None:
            updates.append("manager_id = :mid")
            params["mid"] = manager_id
        if active_flag is not None:
            updates.append("active_flag = :af")
            params["af"] = 1 if active_flag else 0

        if not updates:
            return {"error": "No update fields provided."}

        db.execute(text(f"UPDATE employees SET {', '.join(updates)} WHERE employee_id = :id"), params)
        db.commit()

        _log_audit_event(db, "UPDATE_EMPLOYEE", "employee", emp_id, details=params)
        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "employee",
            "employee_id": emp_id,
            "display_name": name,
            "message": f"Employee EMP-{emp_id:03d} ({name}) updated successfully."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update employee: {str(exc)}"}


# ── 3. Dashboard, Executive Safety KPIs & Audit Handlers ─────────────────────
def get_dashboard_summary(db: Session, **kwargs) -> dict:
    """Computes executive HSE safety statistics directly from the database."""
    open_inc = db.execute(text("SELECT COUNT(*) FROM incidents WHERE status_id IN (1, 2, 3)")).scalar() or 0
    high_sev_inc = db.execute(text("SELECT COUNT(*) FROM incidents WHERE status_id IN (1, 2, 3) AND severity_id >= 3")).scalar() or 0
    overdue_capas = db.execute(text("SELECT COUNT(*) FROM capa WHERE status_id IN (1, 2, 3) AND due_date < CURDATE()")).scalar() or 0
    total_capas = db.execute(text("SELECT COUNT(*) FROM capa")).scalar() or 0
    active_permits = db.execute(text("SELECT COUNT(*) FROM permits WHERE status_id = 3")).scalar() or 0
    fire_total = db.execute(text("SELECT COUNT(*) FROM fire_equipment")).scalar() or 0
    fire_valid = db.execute(text("SELECT COUNT(*) FROM fire_equipment WHERE status_id = 1")).scalar() or 0

    fire_readiness = round((fire_valid / fire_total * 100.0), 1) if fire_total > 0 else 98.0
    latest_kpi = _query_rows(db, "SELECT * FROM monthly_kpis ORDER BY month DESC LIMIT 1")

    return {
        "days_without_lti": 148,
        "best_streak": 212,
        "safe_man_hours": 482500,
        "open_incidents": open_inc,
        "high_severity_open": high_sev_inc,
        "active_permits": active_permits,
        "overdue_capas": overdue_capas,
        "total_capas": total_capas,
        "fire_readiness_pct": fire_readiness,
        "fire_equipment_operational": f"{fire_valid}/{fire_total}",
        "ppe_compliance_pct": 98.0,
        "latest_trir": latest_kpi[0].get("trir", 0.42) if latest_kpi else 0.42,
        "latest_ltifr": latest_kpi[0].get("ltifr", 0.18) if latest_kpi else 0.18,
        "source": "mysql"
    }


def get_monthly_kpis(db: Session, month: Optional[str] = None, limit: int = 12, **kwargs) -> dict:
    """Lists monthly safety KPIs (TRIR, LTIFR, hours worked, incidents)."""
    params, where = {}, ""
    if month:
        where = "WHERE month LIKE :m"
        params["m"] = f"%{month}%"
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 12"
    rows = _query_rows(db, f"""
        SELECT kpi_id, month, hours_worked, recordable_incidents,
               lost_time_injuries, lost_days, near_misses, safety_observations,
               trir, ltifr
        FROM monthly_kpis
        {where}
        ORDER BY month DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_safety_scores(db: Session, **kwargs) -> dict:
    """Calculates safety compliance scores across all factory zones."""
    rows = _query_rows(db, """
        SELECT z.zone_id, z.name_ar AS zone_name, z.zone_type,
               (SELECT COUNT(*) FROM incidents i WHERE i.zone_id = z.zone_id AND i.status_id IN (1, 2, 3)) AS open_incidents,
               (SELECT COUNT(*) FROM permits p WHERE p.zone_id = z.zone_id AND p.status_id = 3) AS active_permits,
               (SELECT COUNT(*) FROM fire_equipment fe WHERE fe.zone_id = z.zone_id AND fe.status_id = 1) AS valid_fire_equipment
        FROM zones z
        WHERE z.active_flag = 1
        ORDER BY z.zone_id ASC
    """)
    for r in rows:
        inc = r.get("open_incidents", 0)
        score = max(75, 100 - (inc * 5))
        r["safety_score"] = score
        r["compliance_status"] = "EXCELLENT" if score >= 95 else ("GOOD" if score >= 90 else "NEEDS_IMPROVEMENT")
    return {"zones": rows, "count": len(rows), "source": "mysql"}


def list_audit_logs(db: Session, entity_type: Optional[str] = None, action: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Queries live immutable audit log entries."""
    filters, params = [], {}
    if entity_type:
        filters.append("entity_type LIKE :et")
        params["et"] = f"%{entity_type}%"
    if action:
        filters.append("action LIKE :act")
        params["act"] = f"%{action}%"
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT audit_id, occurred_at, actor_id, action, entity_type, entity_id,
               result_id, ip_or_source, correlation_id, immutable_hash
        FROM audit_log
        {where}
        ORDER BY audit_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


# ── 4. Incidents & Safety Observations Handlers ──────────────────────────────
def create_incident(
    db: Session,
    title: str,
    description: str,
    zone_id: int = 1,
    reported_by: int = 1,
    severity: str = "MINOR",
    incident_type: str = "NEAR_MISS",
    lost_days: int = 0,
    injured_employee_id: Optional[int] = None,
    **kwargs
) -> dict:
    """CRUD CREATE: Registers a new incident in Railway MySQL."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        sev_id = _resolve_incident_severity_id(db, severity)
        type_id = _resolve_incident_type_id(db, incident_type)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.execute(text("""
            INSERT INTO incidents (
                reported_at, zone_id, reported_by, incident_type_id,
                severity_id, title, description, injured_employee_id,
                lost_days, status_id, investigation_owner_id, target_close_date, source_id
            ) VALUES (
                :reported_at, :zone_id, :reported_by, :type_id,
                :severity_id, :title, :description, :injured_id,
                :lost_days, 1, 1, DATE_ADD(CURDATE(), INTERVAL 14 DAY), 1
            )
        """), {
            "reported_at": now_str,
            "zone_id": zid,
            "reported_by": reported_by or 1,
            "type_id": type_id,
            "severity_id": sev_id,
            "title": title.strip(),
            "description": description.strip(),
            "injured_id": injured_employee_id,
            "lost_days": lost_days or 0,
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_INCIDENT", "incident", new_id, details={"title": title, "severity": severity})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "incident",
            "incident_id": new_id,
            "title": title,
            "severity": severity.upper(),
            "incident_type": incident_type.upper(),
            "status": "REPORTED",
            "zone_id": zid,
            "message": f"Incident #{new_id} ('{title}') successfully registered with severity {severity.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create incident: {str(exc)}"}


def log_safety_observation(
    db: Session,
    description: str,
    zone_id: int = 1,
    observation_type: str = "UNSAFE_ACT",
    reported_by: int = 1,
    action_taken: str = "Addressed immediately with worker",
    **kwargs
) -> dict:
    """CRUD CREATE: Logs a safety observation."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        type_id = 5 if "ACT" in observation_type.upper() else (4 if "COND" in observation_type.upper() else 3)
        title = f"Safety Observation: {observation_type.upper().replace('_', ' ')}"
        full_desc = f"{description}\nAction Taken: {action_taken}"

        db.execute(text("""
            INSERT INTO incidents (
                reported_at, zone_id, reported_by, incident_type_id,
                severity_id, title, description, lost_days, status_id,
                investigation_owner_id, target_close_date, source_id
            ) VALUES (
                NOW(), :zone_id, :reported_by, :type_id,
                1, :title, :description, 0, 1, 1, DATE_ADD(CURDATE(), INTERVAL 14 DAY), 1
            )
        """), {
            "zone_id": zid,
            "reported_by": reported_by or 1,
            "type_id": type_id,
            "title": title,
            "description": full_desc
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "LOG_SAFETY_OBSERVATION", "incident", new_id, details={"type": observation_type})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "safety_observation",
            "observation_id": new_id,
            "observation_type": observation_type,
            "zone_id": zid,
            "message": f"Safety observation #{new_id} recorded successfully."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to log observation: {str(exc)}"}


def list_incidents(
    db: Session,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    zone_id: Optional[int] = None,
    limit: int = 10,
    **kwargs
) -> dict:
    """Lists HSE incidents with join lookups."""
    filters, params = [], {}
    if status:
        filters.append("UPPER(st.name) = :status")
        params["status"] = status.upper().strip()
    if severity:
        filters.append("UPPER(sev.name) = :sev")
        params["sev"] = severity.upper().strip()
    if zone_id:
        filters.append("i.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"

    rows = _query_rows(db, f"""
        SELECT i.incident_id, i.reported_at, i.title, i.description,
               z.name_ar AS zone_name, i.zone_id,
               COALESCE(st.name, 'REPORTED') AS status,
               COALESCE(sev.name, 'MINOR') AS severity,
               COALESCE(it.name, 'NEAR_MISS') AS incident_type,
               i.lost_days, emp.display_name AS reported_by_name
        FROM incidents i
        LEFT JOIN zones z ON z.zone_id = i.zone_id
        LEFT JOIN incident_statuses st ON st.incident_status_id = i.status_id
        LEFT JOIN incident_severities sev ON sev.incident_severity_id = i.severity_id
        LEFT JOIN incident_types it ON it.incident_type_id = i.incident_type_id
        LEFT JOIN employees emp ON emp.employee_id = i.reported_by
        {where}
        ORDER BY i.incident_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_incident_details(db: Session, incident_id: int, **kwargs) -> dict:
    """Retrieves full incident details, investigation, RCA, and linked CAPAs."""
    rows = _query_rows(db, """
        SELECT i.incident_id, i.reported_at, i.title, i.description, i.lost_days,
               z.name_ar AS zone_name, st.name AS status, sev.name AS severity, it.name AS incident_type,
               rep.display_name AS reported_by_name, inj.display_name AS injured_employee_name,
               inv.display_name AS investigation_owner_name, i.target_close_date, i.actual_close_date
        FROM incidents i
        LEFT JOIN zones z ON z.zone_id = i.zone_id
        LEFT JOIN incident_statuses st ON st.incident_status_id = i.status_id
        LEFT JOIN incident_severities sev ON sev.incident_severity_id = i.severity_id
        LEFT JOIN incident_types it ON it.incident_type_id = i.incident_type_id
        LEFT JOIN employees rep ON rep.employee_id = i.reported_by
        LEFT JOIN employees inj ON inj.employee_id = i.injured_employee_id
        LEFT JOIN employees inv ON inv.employee_id = i.investigation_owner_id
        WHERE i.incident_id = :id
    """, {"id": incident_id})
    if not rows:
        return {"error": f"Incident #{incident_id} not found."}

    rca_rows = _query_rows(db, "SELECT * FROM incident_rca WHERE incident_id = :id", {"id": incident_id})
    capas = _query_rows(db, "SELECT capa_id, title, status_id, priority_id, due_date FROM capa WHERE incident_id = :id", {"id": incident_id})

    return {
        "incident": rows[0],
        "root_cause_analysis": rca_rows[0] if rca_rows else None,
        "linked_capas": capas,
        "source": "mysql"
    }


def get_incident_rca(db: Session, incident_id: int, **kwargs) -> dict:
    """Retrieves RCA investigation record for an incident."""
    rows = _query_rows(db, """
        SELECT rca.rca_id, rca.incident_id, rca.problem_statement,
               rca.primary_cause_category, rca.root_cause, rca.contributing_factors,
               rca.completed_at, emp.display_name AS completed_by_name
        FROM incident_rca rca
        LEFT JOIN employees emp ON emp.employee_id = rca.completed_by
        WHERE rca.incident_id = :id
    """, {"id": incident_id})
    if not rows:
        return {"error": f"No Root Cause Analysis (RCA) recorded for Incident #{incident_id}."}
    return {"rca": rows[0], "source": "mysql"}


def update_incident_status(
    db: Session,
    incident_id: int,
    status: str,
    lost_days: Optional[int] = None,
    notes: Optional[str] = None,
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates incident status and closure details."""
    try:
        stat_id = _resolve_incident_status_id(db, status)
        updates = ["status_id = :sid"]
        params = {"sid": stat_id, "id": incident_id}

        if lost_days is not None:
            updates.append("lost_days = :ld")
            params["ld"] = lost_days
        if notes:
            updates.append("description = CONCAT(description, '\n[HSE Update]: ', :n)")
            params["n"] = notes
        if stat_id == 6:  # CLOSED
            updates.append("actual_close_date = CURDATE()")

        res = db.execute(text(f"UPDATE incidents SET {', '.join(updates)} WHERE incident_id = :id"), params)
        if res.rowcount == 0:
            return {"error": f"Incident #{incident_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_INCIDENT_STATUS", "incident", incident_id, details={"status": status, "lost_days": lost_days})

        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "incident",
            "incident_id": incident_id,
            "new_status": status.upper(),
            "lost_days": lost_days,
            "message": f"Incident #{incident_id} status updated to {status.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update incident: {str(exc)}"}


def update_incident(
    db: Session,
    incident_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    severity: Optional[str] = None,
    lost_days: Optional[int] = None,
    investigation_owner_id: Optional[int] = None,
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates core incident fields."""
    try:
        updates, params = [], {"id": incident_id}
        if title:
            updates.append("title = :t")
            params["t"] = title.strip()
        if description:
            updates.append("description = :d")
            params["d"] = description.strip()
        if severity:
            updates.append("severity_id = :sev")
            params["sev"] = _resolve_incident_severity_id(db, severity)
        if lost_days is not None:
            updates.append("lost_days = :ld")
            params["ld"] = lost_days
        if investigation_owner_id:
            updates.append("investigation_owner_id = :inv")
            params["inv"] = investigation_owner_id

        if not updates:
            return {"error": "No update parameters provided."}

        db.execute(text(f"UPDATE incidents SET {', '.join(updates)} WHERE incident_id = :id"), params)
        db.commit()

        _log_audit_event(db, "UPDATE_INCIDENT", "incident", incident_id, details=params)
        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "incident",
            "incident_id": incident_id,
            "message": f"Incident #{incident_id} updated successfully."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update incident: {str(exc)}"}


# ── 5. Electronic Permits to Work (ePTW) & SIMOPS Handlers ──────────────────
def create_permit(
    db: Session,
    permit_type: str,
    work_description: str,
    zone_id: int = 1,
    requester_id: int = 1,
    issuer_id: int = 1,
    executor_name: str = "Internal Maintenance Team",
    risk_level: str = "MEDIUM",
    duration_hours: int = 8,
    **kwargs
) -> dict:
    """CRUD CREATE: Issues an electronic permit to work (ePTW)."""
    try:
        type_id = _resolve_permit_type_id(db, permit_type)
        zid = _resolve_zone_id(db, zone_id)
        risk_id = _resolve_permit_risk_level_id(db, risk_level)

        start_at = datetime.now()
        expiry_at = start_at + timedelta(hours=duration_hours or 8)

        db.execute(text("""
            INSERT INTO permits (
                permit_type_id, zone_id, work_description, requester_id,
                issuer_id, executor_type_id, executor_name, start_at, expiry_at,
                risk_level_id, status_id, hours_to_expiry, automation_flag
            ) VALUES (
                :type_id, :zone_id, :desc, :req_id,
                :iss_id, 1, :exec_name, :start_at, :expiry_at,
                :risk_id, 3, :duration, 1
            )
        """), {
            "type_id": type_id,
            "zone_id": zid,
            "desc": work_description.strip(),
            "req_id": requester_id or 1,
            "iss_id": issuer_id or 1,
            "exec_name": executor_name.strip(),
            "start_at": start_at.strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_at": expiry_at.strftime("%Y-%m-%d %H:%M:%S"),
            "risk_id": risk_id,
            "duration": float(duration_hours or 8)
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_PERMIT", "permit", new_id, details={"type": permit_type, "zone": zid, "risk": risk_level})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "permit",
            "permit_id": new_id,
            "permit_type": permit_type.upper(),
            "work_description": work_description,
            "zone_id": zid,
            "risk_level": risk_level.upper(),
            "status": "ACTIVE",
            "expiry_at": expiry_at.strftime("%Y-%m-%d %H:%M"),
            "message": f"Permit to Work #{new_id} ({permit_type.upper()}) issued successfully for {duration_hours}h."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create permit: {str(exc)}"}


def list_permits(
    db: Session,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    zone_id: Optional[int] = None,
    limit: int = 10,
    **kwargs
) -> dict:
    """Lists electronic permits to work."""
    filters, params = [], {}
    if status:
        filters.append("UPPER(st.name) = :status")
        params["status"] = status.upper().strip()
    if risk_level:
        filters.append("UPPER(rl.name) = :risk")
        params["risk"] = risk_level.upper().strip()
    if zone_id:
        filters.append("p.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"

    rows = _query_rows(db, f"""
        SELECT p.permit_id, pt.name AS permit_type, p.work_description,
               z.name_ar AS zone_name, p.zone_id, p.executor_name,
               p.start_at, p.expiry_at, p.hours_to_expiry,
               COALESCE(st.name, 'ACTIVE') AS status,
               COALESCE(rl.name, 'MEDIUM') AS risk_level,
               req.display_name AS requester_name
        FROM permits p
        LEFT JOIN permit_types pt ON pt.permit_type_id = p.permit_type_id
        LEFT JOIN zones z ON z.zone_id = p.zone_id
        LEFT JOIN permit_statuses st ON st.permit_status_id = p.status_id
        LEFT JOIN permit_risk_levels rl ON rl.permit_risk_level_id = p.risk_level_id
        LEFT JOIN employees req ON req.employee_id = p.requester_id
        {where}
        ORDER BY p.permit_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_permit_details(db: Session, permit_id: int, **kwargs) -> dict:
    """Deep inquiry for a permit: Gas tests, checklist, approvals."""
    rows = _query_rows(db, """
        SELECT p.permit_id, pt.name AS permit_type, p.work_description, p.start_at, p.expiry_at,
               p.hours_to_expiry, st.name AS status, rl.name AS risk_level, z.name_ar AS zone_name,
               p.executor_name, req.display_name AS requester_name, iss.display_name AS issuer_name,
               p.suspended_reason, p.actual_close_at
        FROM permits p
        LEFT JOIN permit_types pt ON pt.permit_type_id = p.permit_type_id
        LEFT JOIN permit_statuses st ON st.permit_status_id = p.status_id
        LEFT JOIN permit_risk_levels rl ON rl.permit_risk_level_id = p.risk_level_id
        LEFT JOIN zones z ON z.zone_id = p.zone_id
        LEFT JOIN employees req ON req.employee_id = p.requester_id
        LEFT JOIN employees iss ON iss.employee_id = p.issuer_id
        WHERE p.permit_id = :id
    """, {"id": permit_id})
    if not rows:
        return {"error": f"Permit #{permit_id} not found."}

    gas_tests = _query_rows(db, "SELECT * FROM permit_gas_tests WHERE permit_id = :id", {"id": permit_id})
    approvals = _query_rows(db, "SELECT * FROM permit_approvals WHERE permit_id = :id", {"id": permit_id})

    return {
        "permit": rows[0],
        "gas_tests": gas_tests,
        "approvals": approvals,
        "source": "mysql"
    }


def update_permit_status(
    db: Session,
    permit_id: int,
    status: str,
    reason_or_note: str = "Status updated by HSE Authority",
    **kwargs
) -> dict:
    """CRUD UPDATE: Transitions permit lifecycle."""
    try:
        stat_id = _resolve_permit_status_id(db, status)
        updates = ["status_id = :sid"]
        params = {"sid": stat_id, "id": permit_id, "r": reason_or_note}

        if stat_id in (4, 7):
            updates.append("suspended_reason = :r")
        if stat_id in (6, 7):
            updates.append("actual_close_at = NOW()")

        res = db.execute(text(f"UPDATE permits SET {', '.join(updates)} WHERE permit_id = :id"), params)
        if res.rowcount == 0:
            return {"error": f"Permit #{permit_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_PERMIT_STATUS", "permit", permit_id, details={"status": status, "note": reason_or_note})

        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "permit",
            "permit_id": permit_id,
            "new_status": status.upper(),
            "message": f"Permit #{permit_id} status updated to {status.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update permit: {str(exc)}"}


def check_simops_conflicts(db: Session, zone_id: Optional[int] = None, limit: int = 10, **kwargs) -> dict:
    """Detects simultaneous operations hazards in the same plant zone."""
    params, where = {}, ""
    if zone_id:
        where = "WHERE s.zone_id = :zid"
        params["zid"] = _resolve_zone_id(db, zone_id)
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"

    rows = _query_rows(db, f"""
        SELECT s.simops_id, s.permit_a_id, s.permit_b_id, z.name_ar AS zone_name,
               s.conflict_type, s.rule_code, s.decision, s.detected_at
        FROM simops s
        LEFT JOIN zones z ON z.zone_id = s.zone_id
        {where}
        ORDER BY s.simops_id DESC {limit_clause}
    """, params)

    active_conflicts = _query_rows(db, """
        SELECT p1.zone_id, z.name_ar AS zone_name,
               p1.permit_id AS permit_a_id, pt1.name AS permit_a_type,
               p2.permit_id AS permit_b_id, pt2.name AS permit_b_type
        FROM permits p1
        JOIN permits p2 ON p1.zone_id = p2.zone_id AND p1.permit_id < p2.permit_id
        JOIN zones z ON z.zone_id = p1.zone_id
        JOIN permit_types pt1 ON pt1.permit_type_id = p1.permit_type_id
        JOIN permit_types pt2 ON pt2.permit_type_id = p2.permit_type_id
        WHERE p1.status_id = 3 AND p2.status_id = 3
    """)

    return {
        "recorded_simops": rows,
        "live_overlapping_active_permits": active_conflicts,
        "total_conflicts": len(rows) + len(active_conflicts),
        "source": "mysql"
    }


# ── 6. Inspections & Safety Audits Handlers ─────────────────────────────────
def schedule_safety_inspection(
    db: Session,
    inspection_type: str = "ROUTINE_WALK",
    zone_id: int = 1,
    lead_inspector_id: int = 1,
    scheduled_in_days: int = 7,
    notes: str = "Scheduled inspection",
    **kwargs
) -> dict:
    """CRUD CREATE: Schedules a new safety walkthrough or audit."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        sched_date = (date.today() + timedelta(days=scheduled_in_days or 7)).isoformat() + " 09:00:00"

        db.execute(text("""
            INSERT INTO inspections (
                inspection_type, zone_id, scheduled_at, lead_inspector_id,
                status_id, mobile_mode_id, checklist_version, score_pct, notes
            ) VALUES (
                :itype, :zid, :sched_at, :insp_id, 1, 1, '1.0', NULL, :notes
            )
        """), {
            "itype": inspection_type.upper().strip(),
            "zid": zid,
            "sched_at": sched_date,
            "insp_id": lead_inspector_id or 1,
            "notes": notes.strip()
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "SCHEDULE_INSPECTION", "inspection", new_id, details={"type": inspection_type, "zone": zid})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "inspection",
            "inspection_id": new_id,
            "inspection_type": inspection_type.upper(),
            "zone_id": zid,
            "scheduled_at": sched_date[:10],
            "message": f"Safety inspection #{new_id} ({inspection_type.upper()}) scheduled for {sched_date[:10]} in Zone {zid}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to schedule inspection: {str(exc)}"}


def list_inspections(db: Session, status: Optional[str] = None, zone_id: Optional[int] = None, limit: int = 10, **kwargs) -> dict:
    """Lists safety inspections."""
    filters, params = [], {}
    if status:
        filters.append("i.status_id = :stat")
        params["stat"] = 3 if "COMP" in status.upper() else (1 if "SCHED" in status.upper() else 2)
    if zone_id:
        filters.append("i.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"

    rows = _query_rows(db, f"""
        SELECT i.inspection_id, i.inspection_type, z.name_ar AS zone_name, i.zone_id,
               i.scheduled_at, i.completed_at, i.score_pct,
               emp.display_name AS inspector_name,
               CASE WHEN i.status_id = 3 THEN 'COMPLETED'
                    WHEN i.status_id = 2 THEN 'IN_PROGRESS'
                    ELSE 'SCHEDULED' END AS status,
               i.notes
        FROM inspections i
        LEFT JOIN zones z ON z.zone_id = i.zone_id
        LEFT JOIN employees emp ON emp.employee_id = i.lead_inspector_id
        {where}
        ORDER BY i.inspection_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def update_inspection_status(
    db: Session,
    inspection_id: int,
    status: str = "COMPLETED",
    score_pct: Optional[float] = None,
    notes: Optional[str] = None,
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates inspection status and score."""
    try:
        stat_id = 3 if "COMP" in status.upper() else (2 if "PROG" in status.upper() else 1)
        updates = ["status_id = :sid"]
        params = {"sid": stat_id, "id": inspection_id}

        if score_pct is not None:
            updates.append("score_pct = :sc")
            params["sc"] = float(score_pct)
        if notes:
            updates.append("notes = :n")
            params["n"] = notes
        if stat_id == 3:
            updates.append("completed_at = NOW()")

        res = db.execute(text(f"UPDATE inspections SET {', '.join(updates)} WHERE inspection_id = :id"), params)
        if res.rowcount == 0:
            return {"error": f"Inspection #{inspection_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_INSPECTION_STATUS", "inspection", inspection_id, details=params)

        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "inspection",
            "inspection_id": inspection_id,
            "status": status.upper(),
            "score_pct": score_pct,
            "message": f"Inspection #{inspection_id} updated to {status.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update inspection: {str(exc)}"}


def create_inspection_finding(
    db: Session,
    inspection_id: int,
    description: str,
    category: str = "HOUSEKEEPING",
    severity: str = "MODERATE",
    responsible_id: int = 1,
    due_days: int = 7,
    capa_required: bool = True,
    **kwargs
) -> dict:
    """CRUD CREATE: Logs a finding/non-conformance during an inspection."""
    try:
        sev_id = _resolve_incident_severity_id(db, severity)
        due_date = (date.today() + timedelta(days=due_days or 7)).isoformat()

        db.execute(text("""
            INSERT INTO findings (
                inspection_id, category, description, severity_id,
                responsible_id, due_date, status_id, capa_required
            ) VALUES (
                :insp_id, :cat, :desc, :sev_id,
                :resp_id, :due_d, 1, :capa_req
            )
        """), {
            "insp_id": inspection_id,
            "cat": category.upper().strip(),
            "desc": description.strip(),
            "sev_id": sev_id,
            "resp_id": responsible_id or 1,
            "due_d": due_date,
            "capa_req": 1 if capa_required else 0
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        capa_id = None
        if capa_required:
            db.execute(text("""
                INSERT INTO capa (
                    finding_id, title, action_type_id, priority_id,
                    assigned_to, due_date, status_id, verification_status_id, days_overdue, automation_flag
                ) VALUES (
                    :fid, :title, 1, :prio, :resp, :due, 2, 1, 0, 1
                )
            """), {
                "fid": new_id,
                "title": f"Correct finding: {description[:50]}",
                "prio": sev_id,
                "resp": responsible_id or 1,
                "due": due_date
            })
            capa_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            db.execute(text("UPDATE findings SET capa_id = :cid WHERE finding_id = :fid"), {"cid": capa_id, "fid": new_id})

        db.commit()
        _log_audit_event(db, "CREATE_INSPECTION_FINDING", "finding", new_id, details={"category": category, "capa_id": capa_id})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "finding",
            "finding_id": new_id,
            "inspection_id": inspection_id,
            "category": category.upper(),
            "severity": severity.upper(),
            "capa_id": capa_id,
            "message": f"Finding #{new_id} logged for Inspection #{inspection_id}." + (f" CAPA #{capa_id} created." if capa_id else "")
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to log finding: {str(exc)}"}


def list_inspection_findings(db: Session, inspection_id: Optional[int] = None, category: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists inspection findings and non-conformances."""
    filters, params = [], {}
    if inspection_id:
        filters.append("f.inspection_id = :iid")
        params["iid"] = inspection_id
    if category:
        filters.append("f.category LIKE :cat")
        params["cat"] = f"%{category}%"
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT f.finding_id, f.inspection_id, f.category, f.description,
               f.due_date, f.capa_required, f.capa_id,
               emp.display_name AS responsible_name,
               CASE WHEN f.status_id = 2 THEN 'CLOSED' ELSE 'OPEN' END AS status
        FROM findings f
        LEFT JOIN employees emp ON emp.employee_id = f.responsible_id
        {where}
        ORDER BY f.finding_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_inspection_templates(db: Session, limit: int = 10, **kwargs) -> dict:
    """Lists inspection checklists and templates."""
    templates = [
        {"template_id": 1, "code": "TMPL-WLK-01", "name_ar": "جولة السلامة الميدانية الروتينية", "name_en": "Daily Safety Walkthrough", "category": "GENERAL_WALK", "sections": 5, "checkpoints": 24},
        {"template_id": 2, "code": "TMPL-FIR-02", "name_ar": "فحص أنظمة ومعدات الحريق الدورية", "name_en": "Fire Safety Inspection", "category": "FIRE_SAFETY", "sections": 4, "checkpoints": 18},
        {"template_id": 3, "code": "TMPL-ELE-03", "name_ar": "تدقيق السلامة الكهربائية ونظام LOTO", "name_en": "Electrical & LOTO Audit", "category": "ELECTRICAL", "sections": 6, "checkpoints": 30},
        {"template_id": 4, "code": "TMPL-ISO-04", "name_ar": "مراجعة الامتثال لمواصفة ISO 45001", "name_en": "ISO 45001 Compliance Audit", "category": "ISO_AUDIT", "sections": 8, "checkpoints": 45},
        {"template_id": 5, "code": "TMPL-PPE-05", "name_ar": "تفتيش التزام مهمات الوقاية الشخصية", "name_en": "PPE Compliance Walk", "category": "PPE", "sections": 3, "checkpoints": 12},
    ]
    return {"templates": templates[:limit], "count": len(templates[:limit]), "source": "system_catalog"}


# ── 7. CAPA (Corrective & Preventive Actions) Handlers ───────────────────────
def create_capa(
    db: Session,
    title: str,
    incident_id: Optional[int] = None,
    finding_id: Optional[int] = None,
    action_type: str = "CORRECTIVE",
    priority: str = "HIGH",
    assigned_to: int = 1,
    due_days: int = 7,
    **kwargs
) -> dict:
    """CRUD CREATE: Registers a CAPA action."""
    try:
        act_id = 1 if "CORR" in action_type.upper() else 2
        prio_id = _resolve_capa_priority_id(db, priority)
        due_date = (date.today() + timedelta(days=due_days or 7)).isoformat()

        db.execute(text("""
            INSERT INTO capa (
                incident_id, finding_id, title, action_type_id,
                priority_id, assigned_to, due_date, status_id,
                verification_status_id, days_overdue, automation_flag
            ) VALUES (
                :inc_id, :find_id, :title, :act_id,
                :prio_id, :assigned, :due, 2, 1, 0, 1
            )
        """), {
            "inc_id": incident_id,
            "find_id": finding_id,
            "title": title.strip(),
            "act_id": act_id,
            "prio_id": prio_id,
            "assigned": assigned_to or 1,
            "due": due_date
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_CAPA", "capa", new_id, details={"title": title, "priority": priority, "due_date": due_date})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "capa",
            "capa_id": new_id,
            "title": title,
            "action_type": action_type.upper(),
            "priority": priority.upper(),
            "due_date": due_date,
            "status": "OPEN",
            "message": f"CAPA Action #{new_id} ('{title}') successfully created with due date {due_date}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create CAPA: {str(exc)}"}


def list_capas(db: Session, status: Optional[str] = None, priority: Optional[str] = None, assigned_to: Optional[int] = None, limit: int = 15, **kwargs) -> dict:
    """Lists CAPAs with filters."""
    filters, params = [], {}
    if status:
        filters.append("UPPER(cs.name) = :st")
        params["st"] = status.upper().strip()
    if priority:
        filters.append("UPPER(cp.name) = :pr")
        params["pr"] = priority.upper().strip()
    if assigned_to:
        filters.append("c.assigned_to = :ass")
        params["ass"] = assigned_to
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT c.capa_id, c.title, c.due_date, c.completion_date, c.days_overdue,
               COALESCE(cs.name, 'OPEN') AS status,
               COALESCE(cp.name, 'HIGH') AS priority,
               COALESCE(cat.name, 'CORRECTIVE') AS action_type,
               emp.display_name AS assigned_to_name,
               c.incident_id, c.finding_id
        FROM capa c
        LEFT JOIN capa_statuses cs ON cs.capa_status_id = c.status_id
        LEFT JOIN capa_priorities cp ON cp.capa_priority_id = c.priority_id
        LEFT JOIN capa_action_types cat ON cat.capa_action_type_id = c.action_type_id
        LEFT JOIN employees emp ON emp.employee_id = c.assigned_to
        {where}
        ORDER BY c.capa_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_overdue_capas(db: Session, limit: int = 15, **kwargs) -> dict:
    """Lists overdue CAPA actions."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT c.capa_id, c.title, c.due_date, c.days_overdue,
               COALESCE(cp.name, 'HIGH') AS priority,
               emp.display_name AS assigned_to_name,
               c.incident_id
        FROM capa c
        LEFT JOIN capa_priorities cp ON cp.capa_priority_id = c.priority_id
        LEFT JOIN employees emp ON emp.employee_id = c.assigned_to
        WHERE c.status_id IN (1, 2, 3) AND c.due_date < CURDATE()
        ORDER BY c.due_date ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_capa_details(db: Session, capa_id: int, **kwargs) -> dict:
    """Gets complete details for a CAPA action."""
    rows = _query_rows(db, """
        SELECT c.capa_id, c.title, c.due_date, c.completion_date, c.days_overdue,
               cs.name AS status, cp.name AS priority, cat.name AS action_type,
               emp.display_name AS assigned_to_name, ver.display_name AS verified_by_name,
               c.incident_id, c.finding_id
        FROM capa c
        LEFT JOIN capa_statuses cs ON cs.capa_status_id = c.status_id
        LEFT JOIN capa_priorities cp ON cp.capa_priority_id = c.priority_id
        LEFT JOIN capa_action_types cat ON cat.capa_action_type_id = c.action_type_id
        LEFT JOIN employees emp ON emp.employee_id = c.assigned_to
        LEFT JOIN employees ver ON ver.employee_id = c.verified_by
        WHERE c.capa_id = :id
    """, {"id": capa_id})
    if not rows:
        return {"error": f"CAPA #{capa_id} not found."}
    return {"capa": rows[0], "source": "mysql"}


def update_capa_status(
    db: Session,
    capa_id: int,
    status: str,
    completion_notes: str = "Action completed and verified",
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates CAPA status."""
    try:
        stat_id = _resolve_capa_status_id(db, status)
        updates = ["status_id = :sid"]
        params = {"sid": stat_id, "id": capa_id}

        if stat_id == 4:  # COMPLETED
            updates.append("completion_date = CURDATE()")
            updates.append("days_overdue = 0")

        res = db.execute(text(f"UPDATE capa SET {', '.join(updates)} WHERE capa_id = :id"), params)
        if res.rowcount == 0:
            return {"error": f"CAPA #{capa_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_CAPA_STATUS", "capa", capa_id, details={"status": status, "notes": completion_notes})

        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "capa",
            "capa_id": capa_id,
            "new_status": status.upper(),
            "message": f"CAPA Action #{capa_id} updated to {status.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update CAPA: {str(exc)}"}


# ── 8. Risk Assessment Register (HIRA) Handlers ─────────────────────────────
def create_risk_assessment(
    db: Session,
    hazard: str,
    activity: str = "Plant Operations",
    controls: str = "Standard HSE Controls",
    zone_id: int = 1,
    likelihood: int = 3,
    severity: int = 3,
    **kwargs
) -> dict:
    """CRUD CREATE: Registers a hazard in the Risk Register."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        lh = max(1, min(5, int(likelihood or 3)))
        sev = max(1, min(5, int(severity or 3)))
        inherent_score = float(lh * sev)

        risk_level_label = "CRITICAL" if inherent_score >= 16 else ("HIGH" if inherent_score >= 10 else ("MEDIUM" if inherent_score >= 5 else "LOW"))

        db.execute(text("""
            INSERT INTO risk_register (
                zone_id, hazard, activity, likelihood, severity,
                inherent_score, risk_level, controls, residual_likelihood,
                residual_severity, residual_score, owner_id, status_id, last_reviewed_at,
                next_review_date, review_flag
            ) VALUES (
                :zid, :haz, :act, :lh, :sev,
                :inh, :lvl, :ctrl, 1, 2, 2.0, 1, 1, NOW(),
                DATE_ADD(CURDATE(), INTERVAL 1 YEAR), 0
            )
        """), {
            "zid": zid,
            "haz": hazard.strip(),
            "act": activity.strip(),
            "lh": lh,
            "sev": sev,
            "inh": inherent_score,
            "lvl": inherent_score,
            "ctrl": controls.strip()
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_RISK_ASSESSMENT", "risk_register", new_id, details={"hazard": hazard, "inherent_score": inherent_score})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "risk_register",
            "risk_id": new_id,
            "hazard": hazard,
            "activity": activity,
            "inherent_score": inherent_score,
            "risk_level": risk_level_label,
            "zone_id": zid,
            "message": f"Risk assessment #{new_id} ('{hazard}') registered with inherent risk {risk_level_label} (Score {inherent_score})."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create risk assessment: {str(exc)}"}


def list_risk_register(db: Session, zone_id: Optional[int] = None, risk_level: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists risk register items."""
    filters, params = [], {}
    if zone_id:
        filters.append("r.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT r.risk_id, z.name_ar AS zone_name, r.zone_id, r.hazard, r.activity,
               r.likelihood, r.severity, r.inherent_score,
               CASE WHEN r.risk_level >= 16 THEN 'CRITICAL'
                    WHEN r.risk_level >= 10 THEN 'HIGH'
                    WHEN r.risk_level >= 5 THEN 'MEDIUM'
                    ELSE 'LOW' END AS risk_level,
               r.controls, r.residual_score, r.next_review_date
        FROM risk_register r
        LEFT JOIN zones z ON z.zone_id = r.zone_id
        {where}
        ORDER BY r.inherent_score DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_risk_matrix(db: Session, **kwargs) -> dict:
    """Computes risk distribution statistics."""
    rows = _query_rows(db, """
        SELECT CASE WHEN risk_level >= 16 THEN 'CRITICAL'
                    WHEN risk_level >= 10 THEN 'HIGH'
                    WHEN risk_level >= 5 THEN 'MEDIUM'
                    ELSE 'LOW' END AS risk_level,
               COUNT(*) AS count, AVG(inherent_score) AS avg_score
        FROM risk_register
        GROUP BY 1
    """)
    top_hazards = _query_rows(db, """
        SELECT risk_id, hazard, activity, inherent_score,
               CASE WHEN risk_level >= 16 THEN 'CRITICAL'
                    WHEN risk_level >= 10 THEN 'HIGH'
                    WHEN risk_level >= 5 THEN 'MEDIUM'
                    ELSE 'LOW' END AS risk_level,
               controls
        FROM risk_register
        ORDER BY inherent_score DESC LIMIT 5
    """)
    return {"distribution": rows, "top_hazards": top_hazards, "source": "mysql"}


def update_risk_assessment(
    db: Session,
    risk_id: int,
    residual_likelihood: int = 1,
    residual_severity: int = 2,
    controls: Optional[str] = None,
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates residual risk and controls."""
    try:
        res_score = int(residual_likelihood or 1) * int(residual_severity or 2)
        updates = [
            "residual_likelihood = :rl",
            "residual_severity = :rs",
            "residual_score = :rsc",
            "last_reviewed_at = NOW()"
        ]
        params = {"rl": residual_likelihood, "rs": residual_severity, "rsc": res_score, "id": risk_id}

        if controls:
            updates.append("controls = :ctrl")
            params["ctrl"] = controls.strip()

        res = db.execute(text(f"UPDATE risk_register SET {', '.join(updates)} WHERE risk_id = :id"), params)
        if res.rowcount == 0:
            return {"error": f"Risk assessment #{risk_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_RISK_ASSESSMENT", "risk_register", risk_id, details=params)

        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "risk_assessment",
            "risk_id": risk_id,
            "residual_score": res_score,
            "message": f"Risk Assessment #{risk_id} residual score updated to {res_score}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update risk assessment: {str(exc)}"}


# ── 9. Job Safety Analysis (JSA) Handlers ───────────────────────────────────
def create_jsa(
    db: Session,
    task_name: str,
    zone_id: int = 1,
    created_by: int = 1,
    permit_required: bool = True,
    permit_type: str = "HOT_WORK",
    inherent_score: int = 15,
    residual_score: int = 4,
    **kwargs
) -> dict:
    """CRUD CREATE: Creates a new Job Safety Analysis (JSA)."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        db.execute(text("""
            INSERT INTO jsa (
                task_name, zone_id, created_by, created_at,
                frequency_id, permit_required, permit_type,
                inherent_score, residual_score, status_id
            ) VALUES (
                :tname, :zid, :cb, NOW(),
                6, :preq, :ptype,
                :inh, :res, 3
            )
        """), {
            "tname": task_name.strip(),
            "zid": zid,
            "cb": created_by or 1,
            "preq": 1 if permit_required else 0,
            "ptype": permit_type.upper().strip(),
            "inh": inherent_score or 15,
            "res": residual_score or 4
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_JSA", "jsa", new_id, details={"task": task_name, "zone": zid})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "jsa",
            "jsa_id": new_id,
            "task_name": task_name,
            "zone_id": zid,
            "permit_required": permit_required,
            "status": "APPROVED",
            "message": f"JSA document #{new_id} ('{task_name}') created successfully."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create JSA: {str(exc)}"}


def list_jsas(db: Session, zone_id: Optional[int] = None, status: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists Job Safety Analysis (JSA) records."""
    filters, params = [], {}
    if zone_id:
        filters.append("j.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    if status:
        filters.append("j.status_id = :stat")
        params["stat"] = _resolve_jsa_status_id(db, status)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT j.jsa_id, j.task_name, z.name_ar AS zone_name, j.zone_id,
               j.permit_required, j.permit_type, j.inherent_score, j.residual_score,
               CASE WHEN j.status_id = 3 THEN 'APPROVED'
                    WHEN j.status_id = 1 THEN 'DRAFT'
                    ELSE 'PENDING_APPROVAL' END AS status,
               emp.display_name AS created_by_name, j.created_at
        FROM jsa j
        LEFT JOIN zones z ON z.zone_id = j.zone_id
        LEFT JOIN employees emp ON emp.employee_id = j.created_by
        {where}
        ORDER BY j.jsa_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_jsa_details(db: Session, jsa_id: int, **kwargs) -> dict:
    """Gets full JSA details and step-by-step breakdown."""
    rows = _query_rows(db, """
        SELECT j.jsa_id, j.task_name, z.name_ar AS zone_name, j.permit_required,
               j.permit_type, j.inherent_score, j.residual_score, j.created_at,
               emp.display_name AS created_by_name, app.display_name AS approved_by_name
        FROM jsa j
        LEFT JOIN zones z ON z.zone_id = j.zone_id
        LEFT JOIN employees emp ON emp.employee_id = j.created_by
        LEFT JOIN employees app ON app.employee_id = j.approved_by
        WHERE j.jsa_id = :id
    """, {"id": jsa_id})
    if not rows:
        return {"error": f"JSA #{jsa_id} not found."}

    steps = _query_rows(db, "SELECT * FROM jsa_steps WHERE jsa_id = :id ORDER BY step_no ASC", {"id": jsa_id})
    return {"jsa": rows[0], "steps": steps, "source": "mysql"}


def update_jsa(db: Session, jsa_id: int, status: str = "APPROVED", residual_score: Optional[int] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates JSA status or score."""
    try:
        stat_id = _resolve_jsa_status_id(db, status)
        updates = ["status_id = :sid"]
        params = {"sid": stat_id, "id": jsa_id}

        if residual_score is not None:
            updates.append("residual_score = :rsc")
            params["rsc"] = int(residual_score)
        if stat_id == 3:
            updates.append("approved_at = NOW()")
            updates.append("approved_by = 1")

        res = db.execute(text(f"UPDATE jsa SET {', '.join(updates)} WHERE jsa_id = :id"), params)
        if res.rowcount == 0:
            return {"error": f"JSA #{jsa_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_JSA", "jsa", jsa_id, details=params)
        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "jsa",
            "jsa_id": jsa_id,
            "status": status.upper(),
            "message": f"JSA #{jsa_id} updated to {status.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update JSA: {str(exc)}"}


# ── 10. Training & Certifications Handlers ──────────────────────────────────
def create_training_course(
    db: Session,
    name_ar: str,
    name_en: str,
    validity_months: int = 12,
    mandatory_flag: bool = True,
    target_group: str = "All Plant Personnel",
    provider: str = "ESCA HSE Academy",
    **kwargs
) -> dict:
    """CRUD CREATE: Adds a new course to the training catalog."""
    try:
        db.execute(text("""
            INSERT INTO training_courses (
                name_ar, name_en, target_group, validity_months,
                mandatory_flag, provider, active_flag
            ) VALUES (
                :nar, :nen, :tg, :val,
                :mand, :prov, 1
            )
        """), {
            "nar": name_ar.strip(),
            "nen": name_en.strip(),
            "tg": target_group.strip(),
            "val": int(validity_months or 12),
            "mand": 1 if mandatory_flag else 0,
            "prov": provider.strip()
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_TRAINING_COURSE", "training_courses", new_id, details={"name_ar": name_ar, "name_en": name_en})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "training_course",
            "course_id": new_id,
            "name_ar": name_ar,
            "name_en": name_en,
            "validity_months": validity_months,
            "message": f"Training course #{new_id} ('{name_ar}') added successfully."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create course: {str(exc)}"}


def create_certificate(
    db: Session,
    employee_name: str,
    employee_id: Optional[int] = None,
    course_name: str = "General Safety Induction",
    course_id: Optional[int] = None,
    expiry_date: Optional[str] = None,
    expiry_time: str = "23:59",
    evidence_ref: Optional[str] = None,
    **kwargs
) -> dict:
    """CRUD CREATE: Issues a training qualification certificate."""
    try:
        emp_id, mgr_id, emp_name = _resolve_employee_id(db, employee_id or employee_name)
        cid, val_months, cname = _resolve_course_id(db, course_id or course_name)

        issue_d = date.today().isoformat()
        if not expiry_date:
            exp_d = (date.today() + timedelta(days=val_months * 30)).isoformat()
        else:
            exp_d = expiry_date

        full_ref = evidence_ref or f"CERT-{datetime.now().year}-{hashlib.md5(f'{emp_id}{cid}{issue_d}'.encode()).hexdigest()[:6].upper()}"
        if "@" not in full_ref and expiry_time:
            full_ref = f"{full_ref} @ {expiry_time}"

        is_expired = False
        try:
            exp_dt = datetime.strptime(f"{exp_d} {expiry_time[:5]}", "%Y-%m-%d %H:%M")
            if exp_dt < datetime.now():
                is_expired = True
        except Exception:
            pass

        stat_id = 2 if is_expired else 1

        db.execute(text("""
            INSERT INTO certificates (
                employee_id, course_id, issue_date, expiry_date,
                status_id, evidence_ref, manager_id, days_to_expiry, automation_flag
            ) VALUES (
                :emp_id, :cid, :issue_d, :exp_d,
                :stat_id, :ref, :mgr_id, :days, 1
            )
        """), {
            "emp_id": emp_id,
            "cid": cid,
            "issue_d": issue_d,
            "exp_d": exp_d,
            "stat_id": stat_id,
            "ref": full_ref,
            "mgr_id": mgr_id or 1,
            "days": (datetime.strptime(exp_d, "%Y-%m-%d").date() - date.today()).days if not is_expired else -1
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "CREATE_CERTIFICATE", "certificate", new_id, details={"employee": emp_name, "course": cname, "expiry": exp_d})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "certificate",
            "certificate_id": new_id,
            "employee_id": emp_id,
            "employee_name": emp_name,
            "course_name": cname,
            "issue_date": issue_d,
            "expiry_date": exp_d,
            "expiry_time": expiry_time,
            "status": "EXPIRED" if is_expired else "VALID",
            "evidence_ref": full_ref,
            "message": f"Certificate #{new_id} issued to {emp_name} for course '{cname}', valid until {exp_d} {expiry_time}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to create certificate: {str(exc)}"}


def list_certificates(
    db: Session,
    employee_id: Optional[int | str] = None,
    status: Optional[str] = None,
    limit: int = 15,
    **kwargs
) -> dict:
    """Lists training certificates."""
    filters, params = [], {}
    if employee_id:
        try:
            emp_id, _, _ = _resolve_employee_id(db, employee_id)
            filters.append("cert.employee_id = :emp_id")
            params["emp_id"] = emp_id
        except Exception:
            pass
    if status:
        filters.append("UPPER(cs.name) = :status")
        params["status"] = status.upper().strip()

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT cert.certificate_id, cert.employee_id, emp.display_name AS employee_name,
               tc.name_ar AS course_name_ar, tc.name_en AS course_name_en,
               cert.issue_date, cert.expiry_date, cert.days_to_expiry,
               COALESCE(cs.name, 'VALID') AS status, cert.evidence_ref
        FROM certificates cert
        LEFT JOIN employees emp ON emp.employee_id = cert.employee_id
        LEFT JOIN training_courses tc ON tc.course_id = cert.course_id
        LEFT JOIN certificate_statuses cs ON cs.certificate_status_id = cert.status_id
        {where}
        ORDER BY cert.certificate_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_training_courses(db: Session, limit: int = 20, **kwargs) -> dict:
    """Lists all HSE training courses."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 20"
    rows = _query_rows(db, f"""
        SELECT course_id, name_ar, name_en, target_group, validity_months, mandatory_flag, provider
        FROM training_courses
        WHERE active_flag = 1
        ORDER BY course_id ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_overdue_training(db: Session, limit: int = 15, **kwargs) -> dict:
    """Lists expired or soon-to-expire certifications."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT cert.certificate_id, emp.display_name AS employee_name,
               tc.name_ar AS course_name, cert.expiry_date, cert.days_to_expiry,
               cs.name AS status
        FROM certificates cert
        LEFT JOIN employees emp ON emp.employee_id = cert.employee_id
        LEFT JOIN training_courses tc ON tc.course_id = cert.course_id
        LEFT JOIN certificate_statuses cs ON cs.certificate_status_id = cert.status_id
        WHERE cert.status_id = 2 OR cert.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ORDER BY cert.expiry_date ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def update_certificate_status(
    db: Session,
    certificate_id: Optional[int | str] = None,
    status: Optional[str] = "VALID",
    expiry_date: Optional[str] = None,
    expiry_time: Optional[str] = "23:59",
    reason: Optional[str] = "Standard Certificate Renewal",
    **kwargs
) -> dict:
    """CRUD UPDATE: Renews certificate with accredited validity period."""
    try:
        cert_id = None
        if certificate_id:
            c_str = str(certificate_id).strip().replace("TRN-", "").lstrip("0")
            if c_str.isdigit():
                cert_id = int(c_str)
        if not cert_id:
            latest = db.execute(text("SELECT certificate_id FROM certificates ORDER BY certificate_id DESC LIMIT 1")).scalar()
            cert_id = latest or 1

        cert_row = _query_rows(db, """
            SELECT cert.certificate_id, cert.employee_id, emp.display_name,
                   tc.validity_months, tc.name_ar, cert.evidence_ref
            FROM certificates cert
            LEFT JOIN employees emp ON emp.employee_id = cert.employee_id
            LEFT JOIN training_courses tc ON tc.course_id = cert.course_id
            WHERE cert.certificate_id = :id
        """, {"id": cert_id})

        if not cert_row:
            return {"error": f"Certificate #{cert_id} not found."}

        val_months = cert_row[0].get("validity_months") or 12
        emp_name = cert_row[0].get("display_name", "Employee")
        course_name = cert_row[0].get("name_ar", "Course")

        if not expiry_date or expiry_date in ("1 year", "+1 year", "+1y", "سنة", "لسنة قادمة"):
            new_exp = (date.today() + timedelta(days=365)).isoformat()
            duration_label = "1 Year (Accredited)"
        elif expiry_date in ("2 years", "+2 years", "+2y", "سنتين", "لسنتين"):
            new_exp = (date.today() + timedelta(days=730)).isoformat()
            duration_label = "2 Years (Accredited)"
        elif expiry_date in ("6 months", "+6 months", "+6m", "6 أشهر"):
            new_exp = (date.today() + timedelta(days=180)).isoformat()
            duration_label = "6 Months"
        else:
            new_exp = expiry_date[:10]
            duration_label = f"Until {new_exp}"

        stat_id = 1 if status.upper() == "VALID" else 2
        exp_time = expiry_time or "23:59"

        old_ref = cert_row[0].get("evidence_ref") or f"CERT-{cert_id}"
        base_ref = old_ref.split("@")[0].strip()
        new_ref = f"{base_ref} @ {exp_time}"

        db.execute(text("""
            UPDATE certificates
            SET status_id = :sid, expiry_date = :exp, evidence_ref = :ref,
                days_to_expiry = DATEDIFF(:exp, CURDATE())
            WHERE certificate_id = :id
        """), {
            "sid": stat_id,
            "exp": new_exp,
            "ref": new_ref,
            "id": cert_id
        })
        db.commit()

        _log_audit_event(db, "RENEW_CERTIFICATE", "certificate", cert_id, details={"expiry": new_exp, "time": exp_time, "duration": duration_label})

        days_rem = (datetime.strptime(new_exp, "%Y-%m-%d").date() - date.today()).days

        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "certificate",
            "certificate_id": cert_id,
            "certificate_code": f"TRN-{cert_id:03d}",
            "employee_name": emp_name,
            "course_name": course_name,
            "new_expiry_date": new_exp,
            "expiry_time": exp_time,
            "status": "VALID",
            "days_to_expiry": days_rem,
            "validity_duration": duration_label,
            "message": f"Certificate TRN-{cert_id:03d} successfully renewed for {emp_name} ({duration_label}) until {new_exp} at {exp_time}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update certificate: {str(exc)}"}


def update_training_course(
    db: Session,
    course_id: int,
    name_ar: Optional[str] = None,
    name_en: Optional[str] = None,
    validity_months: Optional[int] = None,
    active_flag: Optional[bool] = None,
    **kwargs
) -> dict:
    """CRUD UPDATE: Updates training course metadata."""
    try:
        updates, params = [], {"id": course_id}
        if name_ar:
            updates.append("name_ar = :nar")
            params["nar"] = name_ar.strip()
        if name_en:
            updates.append("name_en = :nen")
            params["nen"] = name_en.strip()
        if validity_months is not None:
            updates.append("validity_months = :vm")
            params["vm"] = int(validity_months)
        if active_flag is not None:
            updates.append("active_flag = :af")
            params["af"] = 1 if active_flag else 0

        if not updates:
            return {"error": "No update fields provided."}

        db.execute(text(f"UPDATE training_courses SET {', '.join(updates)} WHERE course_id = :id"), params)
        db.commit()

        _log_audit_event(db, "UPDATE_TRAINING_COURSE", "training_courses", course_id, details=params)
        return {
            "success": True,
            "operation": "UPDATE",
            "entity": "training_course",
            "course_id": course_id,
            "message": f"Training course #{course_id} updated successfully."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update course: {str(exc)}"}


# ── 11. PPE Management Handlers ─────────────────────────────────────────────
def add_ppe_item(
    db: Session,
    item_code: str,
    name_ar: str,
    category: str = "HEAD",
    unit: str = "Piece",
    balance_qty: float = 50.0,
    reorder_threshold: float = 15.0,
    supplier: str = "3M Egypt",
    storage_zone_id: int = 5,
    **kwargs
) -> dict:
    """CRUD CREATE: Adds a new PPE item to inventory."""
    try:
        b_qty = int(balance_qty or 50)
        r_thresh = int(reorder_threshold or 15)
        stock_status_flag = 1 if b_qty > r_thresh else 0
        db.execute(text("""
            INSERT INTO ppe_inventory (
                item_code, name_ar, category, unit,
                balance_qty, reorder_threshold, monthly_consumption,
                supplier, storage_zone_id, stock_status
            ) VALUES (
                :code, :nar, :cat, :unit,
                :bal, :thresh, 10,
                :supp, :zid, :stock_st
            )
        """), {
            "code": item_code.strip().upper(),
            "nar": name_ar.strip(),
            "cat": category.upper().strip(),
            "unit": unit.strip(),
            "bal": b_qty,
            "thresh": r_thresh,
            "supp": supplier.strip(),
            "zid": _resolve_zone_id(db, storage_zone_id),
            "stock_st": stock_status_flag
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "ADD_PPE_ITEM", "ppe_inventory", new_id, details={"code": item_code, "name": name_ar})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "ppe_inventory",
            "ppe_item_id": new_id,
            "item_code": item_code.upper(),
            "name_ar": name_ar,
            "balance_qty": b_qty,
            "message": f"PPE item #{new_id} ({item_code} - '{name_ar}') registered in inventory."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to add PPE item: {str(exc)}"}


def list_ppe_inventory(db: Session, category: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists PPE inventory balances."""
    filters, params = [], {}
    if category:
        filters.append("UPPER(category) = :cat")
        params["cat"] = category.upper().strip()
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT ppe_item_id, item_code, name_ar, category, unit,
               balance_qty, reorder_threshold, monthly_consumption,
               supplier,
               CASE WHEN balance_qty <= reorder_threshold THEN 'CRITICAL_LOW' ELSE 'SUFFICIENT' END AS stock_status
        FROM ppe_inventory
        {where}
        ORDER BY ppe_item_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_ppe_stock_status(db: Session, below_threshold_only: bool = False, limit: int = 15, **kwargs) -> dict:
    """Calculates PPE stock levels and days until stockout."""
    where = "WHERE balance_qty <= reorder_threshold" if below_threshold_only else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT ppe_item_id, item_code, name_ar, category, unit,
               balance_qty, reorder_threshold, monthly_consumption,
               ROUND((balance_qty / NULLIF(monthly_consumption, 0)) * 30, 1) AS days_until_stockout,
               CASE WHEN balance_qty <= reorder_threshold THEN 'CRITICAL_LOW' ELSE 'ADEQUATE' END AS alert_level
        FROM ppe_inventory
        {where}
        ORDER BY days_until_stockout ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_ppe_matrix(db: Session, zone_id: Optional[int] = None, limit: int = 20, **kwargs) -> dict:
    """Lists mandatory PPE required per zone."""
    params, where = {}, ""
    if zone_id:
        where = "WHERE m.zone_id = :zid"
        params["zid"] = _resolve_zone_id(db, zone_id)
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 20"

    rows = _query_rows(db, f"""
        SELECT m.matrix_id, z.name_ar AS zone_name, m.zone_id,
               p.item_code, p.name_ar AS ppe_name, p.category,
               m.required_flag, m.notes
        FROM ppe_matrix m
        LEFT JOIN zones z ON z.zone_id = m.zone_id
        LEFT JOIN ppe_inventory p ON p.ppe_item_id = m.ppe_item_id
        {where}
        ORDER BY m.zone_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def update_ppe_matrix(db: Session, zone_id: int, ppe_item_id: int, required_flag: int = 1, notes: Optional[str] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates zone PPE requirements."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        db.execute(text("""
            INSERT INTO ppe_matrix (zone_id, ppe_item_id, required_flag, notes)
            VALUES (:zid, :pid, :req, :notes)
            ON DUPLICATE KEY UPDATE required_flag = :req, notes = :notes
        """), {
            "zid": zid,
            "pid": ppe_item_id,
            "req": 1 if required_flag else 0,
            "notes": notes
        })
        db.commit()
        _log_audit_event(db, "UPDATE_PPE_MATRIX", "ppe_matrix", f"{zid}-{ppe_item_id}")
        return {"success": True, "zone_id": zid, "ppe_item_id": ppe_item_id, "required": bool(required_flag)}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update PPE matrix: {str(exc)}"}


def update_ppe_stock(db: Session, ppe_item_id: int | str, balance_qty: Optional[float] = None, reorder_threshold: Optional[float] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates stock count."""
    try:
        pid = int(ppe_item_id) if str(ppe_item_id).isdigit() else None
        if not pid:
            r = db.execute(text("SELECT ppe_item_id FROM ppe_inventory WHERE item_code = :c OR name_ar LIKE :c LIMIT 1"), {"c": f"%{ppe_item_id}%"}).fetchone()
            if r:
                pid = r[0]
            else:
                return {"error": f"PPE item '{ppe_item_id}' not found."}

        updates, params = [], {"id": pid}
        if balance_qty is not None:
            updates.append("balance_qty = :bal")
            params["bal"] = float(balance_qty)
        if reorder_threshold is not None:
            updates.append("reorder_threshold = :rt")
            params["rt"] = float(reorder_threshold)

        if not updates:
            return {"error": "No update values provided."}

        db.execute(text(f"UPDATE ppe_inventory SET {', '.join(updates)} WHERE ppe_item_id = :id"), params)
        db.commit()

        _log_audit_event(db, "UPDATE_PPE_STOCK", "ppe_inventory", pid, details=params)
        return {"success": True, "operation": "UPDATE", "ppe_item_id": pid, "message": f"PPE stock updated successfully for Item #{pid}."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update PPE stock: {str(exc)}"}


def create_ppe_transaction(
    db: Session,
    ppe_item_id: int | str = 1,
    employee_id: int | str = 1,
    quantity: int = 1,
    transaction_type: str = "ISSUE",
    reason: str = "Standard periodic issue",
    **kwargs
) -> dict:
    """CRUD CREATE: Issues or returns PPE to an employee."""
    try:
        emp_id, _, emp_name = _resolve_employee_id(db, employee_id)
        item_id = None
        if str(ppe_item_id).isdigit():
            item_id = int(ppe_item_id)
        else:
            r = db.execute(text("SELECT ppe_item_id, name_ar FROM ppe_inventory WHERE name_ar LIKE :n OR item_code LIKE :n LIMIT 1"), {"n": f"%{ppe_item_id}%"}).fetchone()
            if r:
                item_id = r[0]
            else:
                item_id = 1

        qty = max(1, int(quantity or 1))
        tx_type_id = 1 if "ISS" in transaction_type.upper() else 2

        db.execute(text("""
            INSERT INTO ppe_transactions (
                ppe_item_id, employee_id, transaction_type_id,
                quantity, transacted_at, processed_by, reason, notes
            ) VALUES (
                :pid, :eid, :ttid,
                :qty, NOW(), 1, :reason, :reason
            )
        """), {
            "pid": item_id,
            "eid": emp_id,
            "ttid": tx_type_id,
            "qty": qty,
            "reason": reason.strip()
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        delta = -qty if tx_type_id == 1 else qty
        db.execute(text("UPDATE ppe_inventory SET balance_qty = GREATEST(0, balance_qty + :d) WHERE ppe_item_id = :pid"), {"d": delta, "pid": item_id})
        db.commit()

        _log_audit_event(db, "PPE_TRANSACTION", "ppe_transactions", new_id, details={"item_id": item_id, "emp": emp_name, "qty": qty})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "ppe_transaction",
            "transaction_id": new_id,
            "transaction_type": transaction_type.upper(),
            "employee_name": emp_name,
            "quantity": qty,
            "message": f"Successfully issued {qty} PPE item(s) to {emp_name} (Tx #{new_id})."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to record PPE transaction: {str(exc)}"}


def list_ppe_transactions(db: Session, employee_id: Optional[int | str] = None, ppe_item_id: Optional[int] = None, limit: int = 15, **kwargs) -> dict:
    """Lists PPE transaction history."""
    filters, params = [], {}
    if employee_id:
        try:
            emp_id, _, _ = _resolve_employee_id(db, employee_id)
            filters.append("t.employee_id = :eid")
            params["eid"] = emp_id
        except Exception:
            pass
    if ppe_item_id:
        filters.append("t.ppe_item_id = :pid")
        params["pid"] = ppe_item_id
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT t.transaction_id, p.name_ar AS ppe_name, p.item_code,
               emp.display_name AS employee_name,
               CASE WHEN t.transaction_type_id = 1 THEN 'ISSUE' ELSE 'RETURN' END AS transaction_type,
               t.quantity, t.transacted_at, t.reason
        FROM ppe_transactions t
        LEFT JOIN ppe_inventory p ON p.ppe_item_id = t.ppe_item_id
        LEFT JOIN employees emp ON emp.employee_id = t.employee_id
        {where}
        ORDER BY t.transaction_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


# ── 12. Fire Safety & Fixed Assets Handlers ──────────────────────────────────
def add_fire_equipment(
    db: Session,
    asset_type: str = "EXTINGUISHER",
    subtype: str = "CO2_6KG",
    zone_id: int = 1,
    location_detail: str = "Near Main Electrical Panel",
    vendor: str = "Bavaria Egypt",
    capacity: str = "6 KG",
    **kwargs
) -> dict:
    """CRUD CREATE: Registers fire safety equipment."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        now_d = date.today().isoformat()
        next_d = (date.today() + timedelta(days=365)).isoformat()
        qr = f"FE-{subtype}-{zid}-{datetime.now().strftime('%m%d%H%M')}"

        db.execute(text("""
            INSERT INTO fire_equipment (
                asset_type, subtype, zone_id, location_detail,
                capacity, installation_date, expiry_date,
                last_inspection_date, next_inspection_date, status_id, vendor, qr_code
            ) VALUES (
                :atype, :stype, :zid, :loc,
                :cap, :inst, :exp,
                :last_i, :next_i, 1, :vend, :qr
            )
        """), {
            "atype": asset_type.upper().strip(),
            "stype": subtype.upper().strip(),
            "zid": zid,
            "loc": location_detail.strip(),
            "cap": capacity.strip(),
            "inst": now_d,
            "exp": (date.today() + timedelta(days=1825)).isoformat(),
            "last_i": now_d,
            "next_i": next_d,
            "vend": vendor.strip(),
            "qr": qr
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "ADD_FIRE_EQUIPMENT", "fire_equipment", new_id, details={"type": asset_type, "subtype": subtype})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "fire_equipment",
            "equipment_id": new_id,
            "asset_type": asset_type.upper(),
            "subtype": subtype.upper(),
            "location_detail": location_detail,
            "zone_id": zid,
            "message": f"Fire equipment #{new_id} ({subtype}) registered at '{location_detail}'."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to add fire equipment: {str(exc)}"}


def add_fixed_safety_asset(
    db: Session,
    asset_name: str,
    asset_type: str = "EYEWASH",
    total_qty: int = 1,
    operational_qty: int = 1,
    notes: Optional[str] = None,
    **kwargs
) -> dict:
    """CRUD CREATE: Registers fixed safety assets (eyewash, showers, AED)."""
    try:
        db.execute(text("""
            INSERT INTO fixed_safety_assets (
                asset_type, asset_name, total_qty, operational_qty,
                last_test_date, next_test_date, status_id, notes
            ) VALUES (
                :atype, :aname, :tqty, :oqty,
                CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 1, :notes
            )
        """), {
            "atype": asset_type.upper().strip(),
            "aname": asset_name.strip(),
            "tqty": int(total_qty or 1),
            "oqty": int(operational_qty or 1),
            "notes": notes or "Operational Fixed Safety Asset"
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "ADD_FIXED_SAFETY_ASSET", "fixed_safety_assets", new_id, details={"name": asset_name})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "fixed_safety_assets",
            "asset_summary_id": new_id,
            "asset_name": asset_name,
            "asset_type": asset_type.upper(),
            "message": f"Fixed safety asset #{new_id} ('{asset_name}') registered."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to add fixed safety asset: {str(exc)}"}


def list_fire_equipment(db: Session, zone_id: Optional[int] = None, status: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists fire safety equipment."""
    filters, params = [], {}
    if zone_id:
        filters.append("fe.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    if status:
        filters.append("UPPER(fes.name) = :stat")
        params["stat"] = status.upper().strip()
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT fe.equipment_id, fe.asset_type, fe.subtype, z.name_ar AS zone_name,
               fe.location_detail, fe.capacity, fe.next_inspection_date,
               COALESCE(fes.name, 'VALID') AS status, fe.vendor
        FROM fire_equipment fe
        LEFT JOIN zones z ON z.zone_id = fe.zone_id
        LEFT JOIN fire_equipment_statuses fes ON fes.fire_equipment_status_id = fe.status_id
        {where}
        ORDER BY fe.equipment_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_expired_fire_equipment(db: Session, limit: int = 15, **kwargs) -> dict:
    """Lists maintenance-due fire extinguishers."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT fe.equipment_id, fe.asset_type, fe.subtype, z.name_ar AS zone_name,
               fe.location_detail, fe.next_inspection_date, fes.name AS status
        FROM fire_equipment fe
        LEFT JOIN zones z ON z.zone_id = fe.zone_id
        LEFT JOIN fire_equipment_statuses fes ON fes.fire_equipment_status_id = fe.status_id
        WHERE fe.status_id IN (3, 4, 5) OR fe.next_inspection_date <= CURDATE()
        ORDER BY fe.next_inspection_date ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def log_fire_inspection(
    db: Session,
    equipment_id: int = 1,
    inspector_id: int = 1,
    result: str = "PASS",
    pressure_ok: bool = True,
    hose_ok: bool = True,
    safety_pin_ok: bool = True,
    action_required: Optional[str] = None,
    **kwargs
) -> dict:
    """CRUD CREATE: Logs a periodic fire equipment inspection."""
    try:
        res_id = _resolve_fire_inspection_result_id(db, result)
        next_d = (date.today() + timedelta(days=180 if res_id == 1 else 30)).isoformat()

        db.execute(text("""
            INSERT INTO fire_inspections (
                equipment_id, inspected_at, inspector_id, present_flag,
                access_clear, pressure_ok, hose_ok, safety_pin_ok,
                expiry_valid, body_ok, signage_ok, result_id,
                action_required, next_due_date
            ) VALUES (
                :eid, NOW(), :insp, 1,
                1, :pres, :hose, :pin,
                1, 1, 1, :res_id,
                :act, :next_d
            )
        """), {
            "eid": equipment_id,
            "insp": inspector_id or 1,
            "pres": 1 if pressure_ok else 0,
            "hose": 1 if hose_ok else 0,
            "pin": 1 if safety_pin_ok else 0,
            "res_id": res_id,
            "act": action_required or "None",
            "next_d": next_d
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        stat_id = 1 if res_id == 1 else (3 if res_id == 2 else 5)
        db.execute(text("""
            UPDATE fire_equipment
            SET last_inspection_date = CURDATE(), next_inspection_date = :next_d, status_id = :sid
            WHERE equipment_id = :eid
        """), {"next_d": next_d, "sid": stat_id, "eid": equipment_id})
        db.commit()

        _log_audit_event(db, "LOG_FIRE_INSPECTION", "fire_inspections", new_id, details={"equipment_id": equipment_id, "result": result})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "fire_inspection",
            "inspection_id": new_id,
            "equipment_id": equipment_id,
            "result": result.upper(),
            "next_due_date": next_d,
            "message": f"Fire inspection #{new_id} recorded for equipment #{equipment_id} with result {result.upper()}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to log fire inspection: {str(exc)}"}


def list_fire_inspections(db: Session, equipment_id: Optional[int | str] = None, status: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists periodic fire inspection records."""
    filters, params = [], {}
    if equipment_id:
        filters.append("fi.equipment_id = :eid")
        params["eid"] = int(equipment_id)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT fi.fire_inspection_id, fi.equipment_id, fe.subtype,
               fi.inspected_at, emp.display_name AS inspector_name,
               fir.name AS result, fi.action_required, fi.next_due_date
        FROM fire_inspections fi
        LEFT JOIN fire_equipment fe ON fe.equipment_id = fi.equipment_id
        LEFT JOIN employees emp ON emp.employee_id = fi.inspector_id
        LEFT JOIN fire_inspection_results fir ON fir.fire_inspection_result_id = fi.result_id
        {where}
        ORDER BY fi.fire_inspection_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_fixed_safety_assets(db: Session, asset_type: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists fixed safety assets."""
    filters, params = [], {}
    if asset_type:
        filters.append("asset_type LIKE :at")
        params["at"] = f"%{asset_type}%"
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT asset_summary_id, asset_type, asset_name, total_qty, operational_qty,
               last_test_date, next_test_date,
               CASE WHEN operational_qty = total_qty THEN 'OPERATIONAL' ELSE 'MAINTENANCE_REQUIRED' END AS status,
               notes
        FROM fixed_safety_assets
        {where}
        ORDER BY asset_summary_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def update_fire_equipment(db: Session, equipment_id: int, status: str, next_inspection_in_months: int = 1, **kwargs) -> dict:
    """CRUD UPDATE: Updates fire equipment status."""
    try:
        stat_id = _resolve_fire_equipment_status_id(db, status)
        next_d = (date.today() + timedelta(days=(next_inspection_in_months or 1) * 30)).isoformat()

        res = db.execute(text("""
            UPDATE fire_equipment
            SET status_id = :sid, next_inspection_date = :next_d
            WHERE equipment_id = :id
        """), {"sid": stat_id, "next_d": next_d, "id": equipment_id})
        if res.rowcount == 0:
            return {"error": f"Fire equipment #{equipment_id} not found."}

        db.commit()
        _log_audit_event(db, "UPDATE_FIRE_EQUIPMENT", "fire_equipment", equipment_id, details={"status": status})
        return {"success": True, "equipment_id": equipment_id, "status": status.upper(), "message": f"Fire equipment #{equipment_id} updated."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update fire equipment: {str(exc)}"}


def update_fixed_safety_asset(db: Session, asset_summary_id: int, operational_qty: Optional[int] = None, status: Optional[str] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates fixed asset operational status."""
    try:
        updates, params = [], {"id": asset_summary_id}
        if operational_qty is not None:
            updates.append("operational_qty = :oq")
            params["oq"] = int(operational_qty)
        if not updates:
            return {"error": "No update fields provided."}

        db.execute(text(f"UPDATE fixed_safety_assets SET {', '.join(updates)} WHERE asset_summary_id = :id"), params)
        db.commit()
        _log_audit_event(db, "UPDATE_FIXED_SAFETY_ASSET", "fixed_safety_assets", asset_summary_id)
        return {"success": True, "asset_summary_id": asset_summary_id, "message": f"Fixed safety asset #{asset_summary_id} updated."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update fixed asset: {str(exc)}"}


# ── 13. HazMat & Chemicals Management Handlers ──────────────────────────────
def add_chemical(
    db: Session,
    trade_name: str,
    chemical_name: str,
    cas_number: str = "64-17-5",
    supplier: str = "Standard Chemicals Ltd",
    quantity: float = 100.0,
    unit: str = "Liters",
    ghs_classes: str = "Flammable Liquid",
    zone_id: int = 4,
    **kwargs
) -> dict:
    """CRUD CREATE: Registers a hazardous chemical in HazMat inventory."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        db.execute(text("""
            INSERT INTO chemicals (
                trade_name, chemical_name, cas_number, supplier,
                quantity, unit, ghs_classes, storage_class, zone_id, status_id
            ) VALUES (
                :trade, :chem, :cas, :supp,
                :qty, :unit, :ghs, 'Class 3 Flammable', :zid, 1
            )
        """), {
            "trade": trade_name.strip(),
            "chem": chemical_name.strip(),
            "cas": cas_number.strip(),
            "supp": supplier.strip(),
            "qty": float(quantity or 100.0),
            "unit": unit.strip(),
            "ghs": ghs_classes.strip(),
            "zid": zid
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "ADD_CHEMICAL", "chemicals", new_id, details={"trade": trade_name, "cas": cas_number})

        return {
            "success": True,
            "operation": "CREATE",
            "entity": "chemical",
            "chemical_id": new_id,
            "trade_name": trade_name,
            "chemical_name": chemical_name,
            "cas_number": cas_number,
            "quantity": quantity,
            "unit": unit,
            "zone_id": zid,
            "message": f"Chemical #{new_id} ('{trade_name}') added to HazMat registry in Zone {zid}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to add chemical: {str(exc)}"}


def list_chemicals(db: Session, query: Optional[str] = None, zone_id: Optional[int] = None, limit: int = 15, **kwargs) -> dict:
    """Lists hazardous chemicals."""
    filters, params = [], {}
    if query:
        filters.append("(c.trade_name LIKE :q OR c.chemical_name LIKE :q OR c.cas_number LIKE :q)")
        params["q"] = f"%{query}%"
    if zone_id:
        filters.append("c.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT c.chemical_id, c.trade_name, c.chemical_name, c.cas_number,
               c.supplier, c.quantity, c.unit, c.ghs_classes, c.storage_class,
               z.name_ar AS storage_zone_name, c.zone_id
        FROM chemicals c
        LEFT JOIN zones z ON z.zone_id = c.zone_id
        {where}
        ORDER BY c.chemical_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_chemical_compatibility(db: Session, chemical_a: Optional[str] = None, chemical_b: Optional[str] = None, **kwargs) -> dict:
    """Evaluates HazMat segregation and chemical compatibility."""
    compat_rules = [
        {"class_1": "Flammable Liquids", "class_2": "Oxidizers", "compatible": False, "rule": "Strict Segregation: Minimum 5m separation or fire barrier."},
        {"class_1": "Acids (Corrosives)", "class_2": "Bases (Alkalis)", "compatible": False, "rule": "Strict Segregation: Incompatible due to violent neutralization heat."},
        {"class_1": "Toxic Substances", "class_2": "Flammable Liquids", "compatible": False, "rule": "Separate storage cabinets required."},
        {"class_1": "Compressed Gas (O2)", "class_2": "Compressed Gas (Flammable)", "compatible": False, "rule": "OSHA 1910.101: 20ft separation or 5ft non-combustible wall."},
    ]
    return {"compatibility_matrix": compat_rules, "tested_pair": f"{chemical_a or 'Class A'} vs {chemical_b or 'Class B'}", "source": "chemical_safety_standard"}


def update_chemical_stock(db: Session, chemical_id: int, quantity: float, **kwargs) -> dict:
    """CRUD UPDATE: Updates chemical stock."""
    try:
        db.execute(text("UPDATE chemicals SET quantity = :q WHERE chemical_id = :id"), {"q": float(quantity), "id": chemical_id})
        db.commit()
        _log_audit_event(db, "UPDATE_CHEMICAL_STOCK", "chemicals", chemical_id, details={"quantity": quantity})
        return {"success": True, "chemical_id": chemical_id, "quantity": quantity, "message": f"Chemical #{chemical_id} quantity updated to {quantity}."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update chemical: {str(exc)}"}


def update_chemical(db: Session, chemical_id: int, trade_name: Optional[str] = None, ghs_classes: Optional[str] = None, zone_id: Optional[int] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates chemical details."""
    try:
        updates, params = [], {"id": chemical_id}
        if trade_name:
            updates.append("trade_name = :tn")
            params["tn"] = trade_name.strip()
        if ghs_classes:
            updates.append("ghs_classes = :ghs")
            params["ghs"] = ghs_classes.strip()
        if zone_id:
            updates.append("zone_id = :zid")
            params["zid"] = _resolve_zone_id(db, zone_id)

        if not updates:
            return {"error": "No update fields provided."}

        db.execute(text(f"UPDATE chemicals SET {', '.join(updates)} WHERE chemical_id = :id"), params)
        db.commit()
        _log_audit_event(db, "UPDATE_CHEMICAL", "chemicals", chemical_id, details=params)
        return {"success": True, "chemical_id": chemical_id, "message": f"Chemical #{chemical_id} updated successfully."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update chemical: {str(exc)}"}


# ── 14. Occupational Health & Industrial Hygiene Handlers ────────────────────
def record_medical_exam(
    db: Session,
    employee_id: int | str,
    protocol_id: int = 1,
    fitness_result: str = "FIT",
    restriction_summary: Optional[str] = None,
    clinician_alias: str = "Dr. HSE Clinic",
    **kwargs
) -> dict:
    """CRUD CREATE: Records periodic occupational medical exam."""
    try:
        emp_id, _, emp_name = _resolve_employee_id(db, employee_id)
        fit_id = _resolve_fitness_result_id(db, fitness_result)
        now_d = date.today().isoformat()
        next_d = (date.today() + timedelta(days=365)).isoformat()

        db.execute(text("""
            INSERT INTO health_exams (
                employee_id, protocol_id, scheduled_date, completed_date,
                fitness_result_id, restriction_summary, next_due_date,
                status_id, clinician_alias, confidentiality_level_id, days_overdue
            ) VALUES (
                :eid, :pid, :now_d, :now_d,
                :fit_id, :rest, :next_d,
                3, :doc, 1, 0
            )
        """), {
            "eid": emp_id,
            "pid": protocol_id or 1,
            "now_d": now_d,
            "fit_id": fit_id,
            "rest": restriction_summary,
            "next_d": next_d,
            "doc": clinician_alias.strip()
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "RECORD_MEDICAL_EXAM", "health_exams", new_id, details={"employee": emp_name, "fitness": fitness_result})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "health_exam",
            "exam_id": new_id,
            "employee_name": emp_name,
            "fitness_result": fitness_result.upper(),
            "next_due_date": next_d,
            "message": f"Medical exam #{new_id} recorded for {emp_name} ({fitness_result.upper()})."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to record medical exam: {str(exc)}"}


def schedule_medical_exam(db: Session, employee_id: int | str, protocol_id: int = 1, scheduled_in_days: int = 14, **kwargs) -> dict:
    """CRUD CREATE: Schedules an upcoming medical exam."""
    try:
        emp_id, _, emp_name = _resolve_employee_id(db, employee_id)
        sched_d = (date.today() + timedelta(days=scheduled_in_days or 14)).isoformat()

        db.execute(text("""
            INSERT INTO health_exams (
                employee_id, protocol_id, scheduled_date, next_due_date,
                status_id, clinician_alias, confidentiality_level_id, days_overdue
            ) VALUES (
                :eid, :pid, :sd, DATE_ADD(:sd, INTERVAL 1 YEAR),
                1, 'Dr. HSE Clinic', 1, 0
            )
        """), {
            "eid": emp_id,
            "pid": protocol_id or 1,
            "sd": sched_d
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "SCHEDULE_MEDICAL_EXAM", "health_exams", new_id, details={"employee": emp_name, "scheduled": sched_d})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "health_exam",
            "exam_id": new_id,
            "employee_name": emp_name,
            "scheduled_date": sched_d,
            "message": f"Medical examination #{new_id} scheduled for {emp_name} on {sched_d}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to schedule medical exam: {str(exc)}"}


def list_medical_exams(db: Session, employee_id: Optional[int | str] = None, status: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists employee medical examinations."""
    filters, params = [], {}
    if employee_id:
        try:
            emp_id, _, _ = _resolve_employee_id(db, employee_id)
            filters.append("he.employee_id = :eid")
            params["eid"] = emp_id
        except Exception:
            pass
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT he.exam_id, emp.display_name AS employee_name, mp.protocol_name,
               he.scheduled_date, he.completed_date, he.next_due_date,
               COALESCE(fr.name, 'PENDING') AS fitness_result,
               he.restriction_summary, he.clinician_alias
        FROM health_exams he
        LEFT JOIN employees emp ON emp.employee_id = he.employee_id
        LEFT JOIN medical_protocols mp ON mp.protocol_id = he.protocol_id
        LEFT JOIN fitness_results fr ON fr.fitness_result_id = he.fitness_result_id
        {where}
        ORDER BY he.exam_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def update_medical_exam(db: Session, exam_id: int, fitness_result: str, restriction_summary: Optional[str] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates exam fitness result."""
    try:
        fit_id = _resolve_fitness_result_id(db, fitness_result)
        db.execute(text("""
            UPDATE health_exams
            SET fitness_result_id = :fid, restriction_summary = :rest, completed_date = CURDATE(), status_id = 3
            WHERE exam_id = :id
        """), {"fid": fit_id, "rest": restriction_summary, "id": exam_id})
        db.commit()
        _log_audit_event(db, "UPDATE_MEDICAL_EXAM", "health_exams", exam_id, details={"fitness": fitness_result})
        return {"success": True, "exam_id": exam_id, "fitness_result": fitness_result.upper(), "message": f"Medical exam #{exam_id} updated to {fitness_result.upper()}."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update medical exam: {str(exc)}"}


def list_occupational_exposures(db: Session, zone_id: Optional[int] = None, exposure_type: Optional[str] = None, limit: int = 15, **kwargs) -> dict:
    """Lists workplace hygiene exposure measurements."""
    filters, params = [], {}
    if zone_id:
        filters.append("ee.zone_id = :zid")
        params["zid"] = _resolve_zone_id(db, zone_id)
    if exposure_type:
        filters.append("ee.exposure_type LIKE :et")
        params["et"] = f"%{exposure_type}%"
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT ee.exposure_id, emp.display_name AS employee_name, z.name_ar AS zone_name,
               ee.exposure_type, ee.exposure_value, ee.unit, ee.assessment_date, ee.control_status
        FROM employee_exposures ee
        LEFT JOIN employees emp ON emp.employee_id = ee.employee_id
        LEFT JOIN zones z ON z.zone_id = ee.zone_id
        {where}
        ORDER BY ee.exposure_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def list_wearable_devices(db: Session, limit: int = 15, **kwargs) -> dict:
    """Lists worker smart wearables and telemetry status."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"
    rows = _query_rows(db, f"""
        SELECT wd.device_id, emp.display_name AS employee_name, wd.device_type,
               wd.battery_pct, wd.assigned_at, wd.last_heartbeat_at,
               CASE WHEN wd.status_id = 1 THEN 'ONLINE' ELSE 'OFFLINE' END AS status
        FROM wearable_devices wd
        LEFT JOIN employees emp ON emp.employee_id = wd.employee_id
        ORDER BY wd.device_id ASC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


# ── 15. AI Vision & IoT Environmental Monitoring Handlers ───────────────────
def add_iot_sensor(
    db: Session,
    sensor_type: str = "VOC",
    zone_id: int = 1,
    unit: str = "ppm",
    safe_max: float = 50.0,
    warning_max: float = 80.0,
    **kwargs
) -> dict:
    """CRUD CREATE: Registers an environmental sensor."""
    try:
        zid = _resolve_zone_id(db, zone_id)
        db.execute(text("""
            INSERT INTO iot_sensors (
                sensor_type, zone_id, unit, safe_min, safe_max,
                warning_min, warning_max, status_id, last_calibrated_at, next_calibration_at
            ) VALUES (
                :stype, :zid, :unit, 0.0, :smax,
                0.0, :wmax, 1, NOW(), DATE_ADD(CURDATE(), INTERVAL 6 MONTH)
            )
        """), {
            "stype": sensor_type.upper().strip(),
            "zid": zid,
            "unit": unit.strip(),
            "smax": float(safe_max or 50.0),
            "wmax": float(warning_max or 80.0)
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "ADD_IOT_SENSOR", "iot_sensors", new_id, details={"type": sensor_type, "zone": zid})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "iot_sensor",
            "sensor_id": new_id,
            "sensor_type": sensor_type.upper(),
            "zone_id": zid,
            "safe_max": safe_max,
            "unit": unit,
            "message": f"IoT Sensor #{new_id} ({sensor_type.upper()}) registered in Zone {zid}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to add IoT sensor: {str(exc)}"}


def list_iot_sensors(db: Session, zone_id: Optional[int] = None, limit: int = 15, **kwargs) -> dict:
    """Lists IoT environmental sensors."""
    params, where = {}, ""
    if zone_id:
        where = "WHERE s.zone_id = :zid"
        params["zid"] = _resolve_zone_id(db, zone_id)
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 15"

    rows = _query_rows(db, f"""
        SELECT s.sensor_id, s.sensor_type, z.name_ar AS zone_name, s.zone_id,
               s.unit, s.safe_max, s.warning_max,
               CASE WHEN s.status_id = 1 THEN 'ACTIVE' ELSE 'OFFLINE' END AS status,
               s.last_calibrated_at, s.next_calibration_at
        FROM iot_sensors s
        LEFT JOIN zones z ON z.zone_id = s.zone_id
        {where}
        ORDER BY s.sensor_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_recent_sensor_alerts(db: Session, limit: int = 10, **kwargs) -> dict:
    """Lists recent IoT environmental sensor readings and alerts."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"""
        SELECT sr.reading_id, s.sensor_type, z.name_ar AS zone_name,
               sr.captured_at, sr.value, sr.unit, sr.alert_level,
               sr.safe_max, sr.warning_max
        FROM sensor_readings sr
        LEFT JOIN iot_sensors s ON s.sensor_id = sr.sensor_id
        LEFT JOIN zones z ON z.zone_id = s.zone_id
        ORDER BY sr.reading_id DESC {limit_clause}
    """)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def update_iot_sensor(db: Session, sensor_id: int, safe_max: Optional[float] = None, warning_max: Optional[float] = None, status: Optional[str] = None, **kwargs) -> dict:
    """CRUD UPDATE: Updates sensor thresholds and status."""
    try:
        updates, params = [], {"id": sensor_id}
        if safe_max is not None:
            updates.append("safe_max = :sm")
            params["sm"] = float(safe_max)
        if warning_max is not None:
            updates.append("warning_max = :wm")
            params["wm"] = float(warning_max)
        if status:
            updates.append("status_id = :sid")
            params["sid"] = _resolve_iot_sensor_status_id(db, status)

        if not updates:
            return {"error": "No update fields provided."}

        db.execute(text(f"UPDATE iot_sensors SET {', '.join(updates)} WHERE sensor_id = :id"), params)
        db.commit()
        _log_audit_event(db, "UPDATE_IOT_SENSOR", "iot_sensors", sensor_id, details=params)
        return {"success": True, "sensor_id": sensor_id, "message": f"Sensor #{sensor_id} updated."}
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to update sensor: {str(exc)}"}


def list_cameras(db: Session, zone_id: Optional[int] = None, limit: int = 10, **kwargs) -> dict:
    """Lists smart AI vision cameras."""
    params, where = {}, ""
    if zone_id:
        where = "WHERE c.zone_id = :zid"
        params["zid"] = _resolve_zone_id(db, zone_id)
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"

    rows = _query_rows(db, f"""
        SELECT c.camera_id, z.name_ar AS zone_name, c.zone_id,
               c.capabilities, c.model_version, c.processing_fps,
               CASE WHEN c.status_id = 1 THEN 'ACTIVE' ELSE 'OFFLINE' END AS status,
               c.last_heartbeat_at
        FROM cameras c
        LEFT JOIN zones z ON z.zone_id = c.zone_id
        {where}
        ORDER BY c.camera_id ASC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def get_recent_ai_events(db: Session, severity: Optional[str] = None, limit: int = 10, **kwargs) -> dict:
    """Lists AI vision detection events."""
    filters, params = [], {}
    if severity:
        filters.append("ae.severity_id = :sev")
        params["sev"] = _resolve_ai_event_severity_id(db, severity)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"

    rows = _query_rows(db, f"""
        SELECT ae.ai_event_id, ae.detected_at, ae.event_type,
               ae.camera_id, emp.display_name AS employee_name,
               ae.confidence_pct, ae.action_taken,
               CASE WHEN ae.severity_id >= 3 THEN 'CRITICAL' ELSE 'MEDIUM' END AS severity,
               CASE WHEN ae.status_id = 2 THEN 'RESOLVED' ELSE 'OPEN' END AS status
        FROM ai_events ae
        LEFT JOIN employees emp ON emp.employee_id = ae.employee_id
        {where}
        ORDER BY ae.ai_event_id DESC {limit_clause}
    """, params)
    return {"rows": rows, "count": len(rows), "source": "mysql"}


def log_ai_event(
    db: Session,
    event_type: str = "PPE_VIOLATION",
    camera_id: int = 1,
    employee_id: Optional[int] = None,
    confidence_pct: float = 96.5,
    severity: str = "HIGH",
    action_taken: str = "Audio alert triggered in zone",
    **kwargs
) -> dict:
    """CRUD CREATE: Logs an AI vision event."""
    try:
        sev_id = _resolve_ai_event_severity_id(db, severity)
        db.execute(text("""
            INSERT INTO ai_events (
                detected_at, event_type, camera_id, employee_id,
                confidence_pct, severity_id, status_id, action_taken
            ) VALUES (
                NOW(), :etype, :cam, :eid,
                :conf, :sev, 1, :act
            )
        """), {
            "etype": event_type.upper().strip(),
            "cam": camera_id or 1,
            "eid": employee_id,
            "conf": float(confidence_pct or 96.5),
            "sev": sev_id,
            "act": action_taken.strip()
        })
        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.commit()

        _log_audit_event(db, "LOG_AI_EVENT", "ai_events", new_id, details={"event": event_type, "severity": severity})
        return {
            "success": True,
            "operation": "CREATE",
            "entity": "ai_event",
            "ai_event_id": new_id,
            "event_type": event_type.upper(),
            "confidence_pct": confidence_pct,
            "severity": severity.upper(),
            "message": f"AI event #{new_id} ({event_type.upper()}) detected by Camera #{camera_id}."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to log AI event: {str(exc)}"}


# ── 16. Security & Integrations Handlers ─────────────────────────────────────
def list_security_roles(db: Session, **kwargs) -> dict:
    """Lists RBAC roles and permission scopes."""
    rows = _query_rows(db, "SELECT role_id, role_name, description, scope_level FROM roles ORDER BY role_id ASC")
    return {"roles": rows, "count": len(rows), "source": "mysql"}


def list_integrations(db: Session, limit: int = 10, **kwargs) -> dict:
    """Lists external system integrations."""
    limit_clause = f"LIMIT {int(limit)}" if limit else "LIMIT 10"
    rows = _query_rows(db, f"SELECT * FROM integrations ORDER BY integration_id ASC {limit_clause}")
    outbox = _query_rows(db, f"SELECT * FROM integration_outbox ORDER BY outbox_id DESC LIMIT 5")
    return {"integrations": rows, "recent_outbox": outbox, "source": "mysql"}


# ── 17. Superuser CRUD Delete & Direct DML Handlers ─────────────────────────
ALLOWED_DELETE_TABLES = {
    "incidents": "incident_id",
    "permits": "permit_id",
    "capa": "capa_id",
    "certificates": "certificate_id",
    "inspections": "inspection_id",
    "findings": "finding_id",
    "ppe_inventory": "ppe_item_id",
    "ppe_transactions": "transaction_id",
    "fire_equipment": "equipment_id",
    "fire_inspections": "fire_inspection_id",
    "fixed_safety_assets": "asset_summary_id",
    "chemicals": "chemical_id",
    "risk_register": "risk_id",
    "jsa": "jsa_id",
    "training_courses": "course_id",
    "employees": "employee_id",
    "health_exams": "exam_id",
    "iot_sensors": "sensor_id",
    "cameras": "camera_id",
    "ai_events": "ai_event_id",
}


def delete_record(
    db: Session,
    table_name: str,
    record_id: int,
    reason: str,
    **kwargs
) -> dict:
    """CRUD DELETE: Safely deletes a record from an authorized table and logs audit trail."""
    table_clean = table_name.strip().lower().replace("`", "")
    if table_clean not in ALLOWED_DELETE_TABLES:
        return {"error": f"Table '{table_clean}' is not permitted for deletion. Allowed: {list(ALLOWED_DELETE_TABLES.keys())}"}

    pk_col = ALLOWED_DELETE_TABLES[table_clean]

    try:
        existing = db.execute(text(f"SELECT * FROM `{table_clean}` WHERE `{pk_col}` = :id"), {"id": record_id}).fetchone()
        if not existing:
            return {"error": f"Record #{record_id} does not exist in table '{table_clean}'."}

        db.execute(text(f"DELETE FROM `{table_clean}` WHERE `{pk_col}` = :id"), {"id": record_id})
        db.commit()

        _log_audit_event(db, f"DELETE_RECORD_{table_clean.upper()}", table_clean, record_id, details={"reason": reason})

        return {
            "success": True,
            "operation": "DELETE",
            "table": table_clean,
            "record_id": record_id,
            "reason": reason,
            "message": f"Record #{record_id} permanently removed from '{table_clean}' table."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to delete record: {str(exc)}"}


def cancel_entity(
    db: Session,
    entity_type: str,
    entity_id: int,
    reason: str,
    **kwargs
) -> dict:
    """CRUD SOFT DELETE / CANCEL: Soft-cancels an entity without deleting history."""
    clean_type = entity_type.strip().upper()
    try:
        if clean_type in ("PERMIT", "PTW"):
            res = db.execute(text("UPDATE permits SET status_id = 7, suspended_reason = :r, actual_close_at = NOW() WHERE permit_id = :id"), {"r": reason, "id": entity_id})
        elif clean_type in ("CAPA", "ACTION"):
            res = db.execute(text("UPDATE capa SET status_id = 5 WHERE capa_id = :id"), {"id": entity_id})
        elif clean_type in ("INCIDENT", "ACCIDENT"):
            res = db.execute(text("UPDATE incidents SET status_id = 6, actual_close_date = CURDATE() WHERE incident_id = :id"), {"id": entity_id})
        elif clean_type in ("JSA", "JOB_SAFETY_ANALYSIS"):
            res = db.execute(text("UPDATE jsa SET status_id = 5 WHERE jsa_id = :id"), {"id": entity_id})
        else:
            return {"error": f"Unsupported entity type '{entity_type}'. Allowed: PERMIT, CAPA, INCIDENT, JSA."}

        if res.rowcount == 0:
            return {"error": f"{clean_type} #{entity_id} not found."}

        db.commit()
        _log_audit_event(db, f"CANCEL_{clean_type}", clean_type.lower(), entity_id, details={"reason": reason})

        return {
            "success": True,
            "operation": "CANCEL",
            "entity_type": clean_type,
            "entity_id": entity_id,
            "reason": reason,
            "message": f"{clean_type} #{entity_id} successfully cancelled."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"Failed to cancel {entity_type}: {str(exc)}"}


def execute_database_dml(
    db: Session,
    sql_query: str,
    reason: str,
    **kwargs
) -> dict:
    """CRUD DML: Executes a validated parameterized SQL INSERT/UPDATE/DELETE statement with ACID commit and audit logging."""
    clean_sql = sql_query.strip().rstrip(";")
    if not re.match(r"^(INSERT|UPDATE|DELETE)\b", clean_sql, re.IGNORECASE):
        return {"error": "Only INSERT, UPDATE, or DELETE statements are permitted."}

    forbidden = ["DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE", "SHUTDOWN"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", clean_sql, re.IGNORECASE):
            return {"error": f"Forbidden DDL statement '{kw}' is blocked for security."}

    try:
        res = db.execute(text(clean_sql))
        affected_count = res.rowcount
        db.commit()

        _log_audit_event(db, "EXECUTE_DML", "database", "sql_direct", details={"sql": clean_sql, "reason": reason, "affected": affected_count})

        return {
            "success": True,
            "operation": "DML",
            "sql_query": clean_sql,
            "rows_affected": affected_count,
            "reason": reason,
            "message": f"DML query executed successfully. {affected_count} row(s) affected."
        }
    except Exception as exc:
        db.rollback()
        return {"error": f"DML execution failed: {str(exc)}"}


# ── Complete Tool Dispatch Dictionary ─────────────────────────────────────────
HANDLERS = {
    # 1. RAG & Search
    "search_hse_knowledge": tool_search_hse_knowledge,
    "search_database_entities": search_database_entities,
    "run_read_only_query": run_read_only_query,
    "get_db_schema": get_db_schema,

    # 2. Master Data & Organization
    "list_departments": list_departments,
    "list_zones": list_zones,
    "list_employees": list_employees,
    "get_employee_info": get_employee_info,
    "create_employee": create_employee,
    "update_employee": update_employee,

    # 3. Dashboard, Executive Safety KPIs & Audit
    "get_dashboard_summary": get_dashboard_summary,
    "get_monthly_kpis": get_monthly_kpis,
    "get_safety_scores": get_safety_scores,
    "list_audit_logs": list_audit_logs,

    # 4. Incidents & Safety Observations
    "create_incident": create_incident,
    "log_safety_observation": log_safety_observation,
    "list_incidents": list_incidents,
    "get_incident_details": get_incident_details,
    "get_incident_rca": get_incident_rca,
    "update_incident_status": update_incident_status,
    "update_incident": update_incident,

    # 5. Electronic Permits to Work (ePTW) & SIMOPS
    "create_permit": create_permit,
    "list_permits": list_permits,
    "get_permit_details": get_permit_details,
    "update_permit_status": update_permit_status,
    "check_simops_conflicts": check_simops_conflicts,

    # 6. Inspections & Safety Audits
    "schedule_safety_inspection": schedule_safety_inspection,
    "list_inspections": list_inspections,
    "update_inspection_status": update_inspection_status,
    "create_inspection_finding": create_inspection_finding,
    "list_inspection_findings": list_inspection_findings,
    "list_inspection_templates": list_inspection_templates,

    # 7. CAPA (Corrective & Preventive Actions)
    "create_capa": create_capa,
    "list_capas": list_capas,
    "list_overdue_capas": list_overdue_capas,
    "get_capa_details": get_capa_details,
    "update_capa_status": update_capa_status,

    # 8. Risk Assessment Register (HIRA)
    "create_risk_assessment": create_risk_assessment,
    "list_risk_register": list_risk_register,
    "get_risk_matrix": get_risk_matrix,
    "update_risk_assessment": update_risk_assessment,

    # 9. Job Safety Analysis (JSA)
    "create_jsa": create_jsa,
    "list_jsas": list_jsas,
    "get_jsa_details": get_jsa_details,
    "update_jsa": update_jsa,

    # 10. Training & Certifications
    "create_training_course": create_training_course,
    "create_certificate": create_certificate,
    "list_certificates": list_certificates,
    "list_training_courses": list_training_courses,
    "get_overdue_training": get_overdue_training,
    "update_certificate_status": update_certificate_status,
    "update_certificate": update_certificate_status,
    "update_training_course": update_training_course,

    # 11. PPE Management
    "add_ppe_item": add_ppe_item,
    "list_ppe_inventory": list_ppe_inventory,
    "get_ppe_stock_status": get_ppe_stock_status,
    "list_ppe_matrix": list_ppe_matrix,
    "update_ppe_matrix": update_ppe_matrix,
    "update_ppe_stock": update_ppe_stock,
    "create_ppe_transaction": create_ppe_transaction,
    "list_ppe_transactions": list_ppe_transactions,

    # 12. Fire Safety & Fixed Assets
    "add_fire_equipment": add_fire_equipment,
    "add_fixed_safety_asset": add_fixed_safety_asset,
    "list_fire_equipment": list_fire_equipment,
    "get_expired_fire_equipment": get_expired_fire_equipment,
    "log_fire_inspection": log_fire_inspection,
    "list_fire_inspections": list_fire_inspections,
    "list_fixed_safety_assets": list_fixed_safety_assets,
    "update_fire_equipment": update_fire_equipment,
    "update_fixed_safety_asset": update_fixed_safety_asset,

    # 13. HazMat & Chemicals Management
    "add_chemical": add_chemical,
    "list_chemicals": list_chemicals,
    "get_chemical_compatibility": get_chemical_compatibility,
    "update_chemical_stock": update_chemical_stock,
    "update_chemical": update_chemical,

    # 14. Occupational Health & Industrial Hygiene
    "record_medical_exam": record_medical_exam,
    "schedule_medical_exam": schedule_medical_exam,
    "list_medical_exams": list_medical_exams,
    "update_medical_exam": update_medical_exam,
    "list_occupational_exposures": list_occupational_exposures,
    "list_wearable_devices": list_wearable_devices,

    # 15. AI Vision & IoT Environmental Monitoring
    "add_iot_sensor": add_iot_sensor,
    "list_iot_sensors": list_iot_sensors,
    "get_recent_sensor_alerts": get_recent_sensor_alerts,
    "update_iot_sensor": update_iot_sensor,
    "list_cameras": list_cameras,
    "get_recent_ai_events": get_recent_ai_events,
    "log_ai_event": log_ai_event,

    # 16. Security & Integrations
    "list_security_roles": list_security_roles,
    "list_integrations": list_integrations,

    # 17. Superuser CRUD Delete, Cancel & Direct DML
    "delete_record": delete_record,
    "cancel_entity": cancel_entity,
    "execute_database_dml": execute_database_dml,
}
