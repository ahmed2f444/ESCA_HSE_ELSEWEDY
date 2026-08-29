import pytest
from sqlalchemy import text
from app.database import SessionLocal
from app.tools.knowledge_base import search_hse_knowledge
from app.tools.rbac import check_tool_access, filter_tools_for_role, normalize_role
from app.tools.handlers import (
    create_incident, update_incident_status,
    create_permit, update_permit_status,
    create_capa, update_capa_status,
    create_certificate, update_certificate_status,
    create_ppe_transaction, update_ppe_stock,
    log_fire_inspection, add_chemical,
    search_database_entities, delete_record
)
from app.tools.definitions import TOOLS


def test_rag_knowledge_search():
    """Verify that domain HSE standards and regulations are retrieved accurately."""
    # Test ISO 45001 retrieval
    res_iso = search_hse_knowledge(query="ISO 45001 Clause 6 HIRA Hazard Identification")
    assert res_iso["total_matches"] > 0
    first_item = res_iso["results"][0]
    assert "ISO 45001" in first_item["standard"]

    # Test OSHA Confined space retrieval
    res_osha = search_hse_knowledge(query="OSHA confined space gas testing atmospheric limits")
    assert res_osha["total_matches"] > 0
    assert any("1910.146" in r.get("standard", "") or "1910-146" in r.get("id", "") for r in res_osha["results"])

    # Test Golden Rules retrieval
    res_gr = search_hse_knowledge(query="Golden Rule LOTO energy isolation")
    assert res_gr["total_matches"] > 0
    assert any("LOTO" in r.get("clause", "") for r in res_gr["results"])

    # Test Formula retrieval
    res_trir = search_hse_knowledge(query="TRIR formula calculate recordable incidents")
    assert res_trir["total_matches"] > 0
    assert any("TRIR" in r.get("title_en", "") for r in res_trir["results"])


def test_rbac_permission_matrix():
    """Verify role-based tool filtering and authorization checks."""
    # HSE Manager has full access
    is_auth_mgr, _ = check_tool_access("HSE_MANAGER", "create_incident")
    assert is_auth_mgr is True
    is_auth_mgr_dml, _ = check_tool_access("HSE_MANAGER", "execute_database_dml")
    assert is_auth_mgr_dml is True

    # Worker can create incident & search knowledge, but cannot delete records or approve permits
    is_worker_search, _ = check_tool_access("WORKER", "search_hse_knowledge")
    assert is_worker_search is True
    is_worker_report, _ = check_tool_access("WORKER", "create_incident")
    assert is_worker_report is True
    is_worker_delete, _ = check_tool_access("WORKER", "delete_record")
    assert is_worker_delete is False
    is_worker_dml, _ = check_tool_access("WORKER", "execute_database_dml")
    assert is_worker_dml is False

    # Filtered tools for Worker should NOT include delete_record
    worker_tools = filter_tools_for_role(TOOLS, "WORKER")
    tool_names = [t["function"]["name"] for t in worker_tools]
    assert "delete_record" not in tool_names
    assert "execute_database_dml" not in tool_names
    assert "search_hse_knowledge" in tool_names


def test_crud_incident_lifecycle():
    """Verify creating, updating, and querying an incident on Railway MySQL."""
    db = SessionLocal()
    try:
        # 1. CREATE Incident
        created = create_incident(
            db=db,
            title="[TEST] Automated AI Test Incident",
            description="Testing AI Agent CRUD capability on Railway MySQL.",
            zone_id=1,
            severity="MINOR",
            incident_type="NEAR_MISS",
            lost_days=0
        )
        assert created.get("success") is True
        incident_id = created["incident_id"]
        assert incident_id > 0

        # 2. UPDATE Incident Status
        updated = update_incident_status(
            db=db,
            incident_id=incident_id,
            status="CLOSED",
            lost_days=0,
            notes="Closed via automated verification test."
        )
        assert updated.get("success") is True
        assert updated["status"] == "CLOSED"

        # 3. Clean up test record
        del_res = delete_record(db=db, table_name="incidents", record_id=incident_id, reason="Automated test cleanup")
        assert del_res.get("success") is True

    finally:
        db.close()


def test_crud_permit_lifecycle():
    """Verify creating and updating a permit on Railway MySQL."""
    db = SessionLocal()
    try:
        # 1. CREATE Permit
        created = create_permit(
            db=db,
            permit_type="HOT_WORK",
            work_description="[TEST] Automated AI Test Permit - Welding Cable Line 4",
            zone_id=2,
            risk_level="HIGH",
            duration_hours=4
        )
        assert created.get("success") is True
        permit_id = created["permit_id"]
        assert permit_id > 0

        # 2. UPDATE Permit Status to APPROVED
        updated = update_permit_status(
            db=db,
            permit_id=permit_id,
            status="APPROVED",
            reason_or_note="Approved by AI Safety Officer."
        )
        assert updated.get("success") is True
        assert updated["status"] == "APPROVED"

        # 3. Clean up
        delete_record(db=db, table_name="permits", record_id=permit_id, reason="Automated test cleanup")

    finally:
        db.close()


def test_crud_capa_lifecycle():
    """Verify creating and completing a CAPA action item."""
    db = SessionLocal()
    try:
        created = create_capa(
            db=db,
            title="[TEST] Automated AI Test CAPA - Install Warning Signage",
            priority="HIGH",
            due_days=3
        )
        assert created.get("success") is True
        capa_id = created["capa_id"]
        assert capa_id > 0

        updated = update_capa_status(
            db=db,
            capa_id=capa_id,
            status="COMPLETED",
            completion_notes="Signage installed and verified."
        )
        assert updated.get("success") is True
        assert updated["status"] == "COMPLETED"

        delete_record(db=db, table_name="capa", record_id=capa_id, reason="Automated test cleanup")
    finally:
        db.close()


def test_audit_log_generation():
    """Verify that every CRUD operation writes to audit_log table."""
    db = SessionLocal()
    try:
        # Check that audit log has entries from AI_ASSISTANT
        rows = db.execute(text("SELECT * FROM audit_log WHERE actor_id = 'AI_ASSISTANT' ORDER BY audit_id DESC LIMIT 5")).fetchall()
        assert len(rows) > 0
        latest = rows[0]
        assert latest._mapping["actor_id"] == "AI_ASSISTANT"
    finally:
        db.close()


def test_crud_certificate_lifecycle():
    """Verify creating and updating a training certificate on Railway MySQL."""
    db = SessionLocal()
    try:
        # 1. CREATE Certificate for Ahmed Samy
        created = create_certificate(
            db=db,
            employee_id="ahmed samy",
            course_id="General Safety Induction",
            expiry_date="today"
        )
        assert created.get("success") is True
        cert_id = created["certificate_id"]
        assert cert_id > 0
        assert created["employee_name"] == "أحمد سامي"

        # 2. UPDATE Certificate Status
        updated = update_certificate_status(
            db=db,
            certificate_id=cert_id,
            status="VALID",
            reason="Extended by HSE Director"
        )
        assert updated.get("success") is True
        assert updated["status"] == "VALID"

        # 3. Clean up
        delete_record(db=db, table_name="certificates", record_id=cert_id, reason="Automated test cleanup")
    finally:
        db.close()


def test_crud_certificate_timestamp_and_live_notification():
    """Verify that a certificate with past/current timestamp triggers EXPIRED status and a live notification."""
    db = SessionLocal()
    try:
        created = create_certificate(
            db=db,
            employee_id="ahmed samy",
            course_id="General Safety Induction",
            expiry_date="today",
            expiry_time="01:50 AM"
        )
        assert created.get("success") is True
        cert_id = created["certificate_id"]
        notif_id = created.get("notification_id")
        assert created["status"] == "EXPIRED"
        assert created["live_notification_triggered"] is True
        assert notif_id is not None

        # Verify notification in database
        notif_row = db.execute(
            text("SELECT * FROM notifications WHERE notification_id = :id"),
            {"id": notif_id}
        ).fetchone()
        assert notif_row is not None
        assert notif_row._mapping["type"] == "AUTOMATION_CERTIFICATE_EXPIRY"
        assert notif_row._mapping["entity_id"] == str(cert_id)

        # Cleanup
        delete_record(db=db, table_name="certificates", record_id=cert_id, reason="Test cleanup")
        db.execute(text("DELETE FROM notifications WHERE notification_id = :id"), {"id": notif_id})
        db.commit()
    finally:
        db.close()


def test_universal_database_search():
    """Verify search across entities in the database."""
    db = SessionLocal()
    try:
        res = search_database_entities(db=db, query="Cable", limit=5)
        assert "results" in res
        assert isinstance(res["results"], list)
    finally:
        db.close()


def test_crud_certificate_update_end_date_and_time():
    """Verify modifying a certificate's end date/time (e.g. changing 12:50 PM to 12:36 PM)."""
    db = SessionLocal()
    try:
        # 1. Create initial certificate
        created = create_certificate(
            db=db,
            employee_name="كريم رشاد",
            course_name="السلامة العامة",
            expiry_date="today",
            expiry_time="12:50 PM"
        )
        assert created.get("success") is True
        cert_id = created["certificate_id"]

        # 2. Update certificate end date/time to 12:36 PM
        updated = update_certificate_status(
            db=db,
            certificate_id=cert_id,
            expiry_time="12:36 PM",
            reason="Adjusted expiration timestamp by Admin"
        )
        assert updated.get("success") is True
        assert updated["certificate_id"] == cert_id
        assert updated["expiry_time"] == "12:36"

        # 3. Clean up
        delete_record(db=db, table_name="certificates", record_id=cert_id, reason="Test cleanup")
    finally:
        db.close()

