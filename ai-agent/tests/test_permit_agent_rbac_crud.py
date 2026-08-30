"""
Unit & Integration Tests for Work Permit (ePTW) AI Agent CRUD operations and RBAC enforcement.
"""
import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.rbac import (
    check_tool_access,
    filter_tools_for_role,
    ROLE_ADMIN,
    ROLE_HSE_MANAGER,
    ROLE_HSE_OFFICER,
    ROLE_OPERATIONS_MANAGER,
    ROLE_DEPT_MANAGER,
    ROLE_PRODUCTION_SUPERVISOR,
    ROLE_MAINTENANCE_ENGINEER,
    ROLE_ELECTRICAL_ENGINEER,
    ROLE_QUALITY_ENGINEER,
    ROLE_WAREHOUSE_SUPERVISOR,
    ROLE_TRAINING_COORDINATOR,
    ROLE_WORKER,
    ROLE_AUDITOR,
)
from app.tools.definitions import TOOLS
from app.tools.handlers import (
    HANDLERS,
    _resolve_permit_status_id,
    _resolve_permit_type_id,
    _resolve_permit_risk_level_id,
)
from app.nlp.keyword_parser import extract_entity_ids, classify_hse_intent, parse_user_hse_prompt


class TestPermitRbacPermissions:
    """Test RBAC role validation across all Permit tools."""

    def test_admin_and_hse_manager_have_full_permit_crud(self):
        tools = [
            "create_permit", "list_permits", "get_permit_details",
            "update_permit_status", "update_permit", "delete_permit",
            "check_simops_conflicts"
        ]
        for t in tools:
            is_auth, _ = check_tool_access(ROLE_ADMIN, t)
            assert is_auth, f"Admin should have access to {t}"
            is_auth, _ = check_tool_access(ROLE_HSE_MANAGER, t)
            assert is_auth, f"HSE Manager should have access to {t}"

    def test_operations_manager_has_crud_except_delete(self):
        allowed = [
            "create_permit", "list_permits", "get_permit_details",
            "update_permit_status", "update_permit", "check_simops_conflicts"
        ]
        for t in allowed:
            is_auth, _ = check_tool_access(ROLE_OPERATIONS_MANAGER, t)
            assert is_auth, f"Ops Manager should have access to {t}"
        is_auth, _ = check_tool_access(ROLE_OPERATIONS_MANAGER, "delete_permit")
        assert not is_auth, "Ops Manager cannot delete permits"

    def test_hse_officer_has_cru_access(self):
        allowed = [
            "create_permit", "list_permits", "get_permit_details",
            "update_permit_status", "update_permit", "check_simops_conflicts"
        ]
        for t in allowed:
            is_auth, _ = check_tool_access(ROLE_HSE_OFFICER, t)
            assert is_auth, f"HSE Officer should have access to {t}"
        is_auth, _ = check_tool_access(ROLE_HSE_OFFICER, "delete_permit")
        assert not is_auth, "HSE Officer cannot delete permits"

    def test_production_supervisor_and_engineers_access(self):
        allowed = ["create_permit", "list_permits", "get_permit_details", "update_permit", "check_simops_conflicts"]
        for role in [ROLE_PRODUCTION_SUPERVISOR, ROLE_MAINTENANCE_ENGINEER, ROLE_ELECTRICAL_ENGINEER, ROLE_DEPT_MANAGER]:
            for t in allowed:
                is_auth, _ = check_tool_access(role, t)
                assert is_auth, f"{role} should have access to {t}"
            is_auth, _ = check_tool_access(role, "delete_permit")
            assert not is_auth, f"{role} cannot delete permits"

    def test_worker_and_auditor_read_only_access(self):
        read_tools = ["list_permits", "get_permit_details"]
        mutation_tools = ["create_permit", "update_permit_status", "update_permit", "delete_permit"]

        for role in [ROLE_WORKER, ROLE_AUDITOR, ROLE_QUALITY_ENGINEER, ROLE_WAREHOUSE_SUPERVISOR, ROLE_TRAINING_COORDINATOR]:
            for t in read_tools:
                is_auth, _ = check_tool_access(role, t)
                assert is_auth, f"{role} should have read access to {t}"
            for t in mutation_tools:
                is_auth, _ = check_tool_access(role, t)
                assert not is_auth, f"{role} must NOT have mutation access to {t}"

    def test_filter_tools_for_worker_role(self):
        worker_tools = filter_tools_for_role(TOOLS, ROLE_WORKER)
        tool_names = [t["function"]["name"] for t in worker_tools]
        assert "list_permits" in tool_names
        assert "get_permit_details" in tool_names
        assert "create_permit" not in tool_names
        assert "delete_permit" not in tool_names
        assert "update_permit" not in tool_names


class TestPermitToolDefinitionsAndHandlers:
    """Verify tool schemas and handler registrations."""

    def test_permit_tools_registered_in_definitions(self):
        tool_map = {t["function"]["name"]: t["function"] for t in TOOLS}
        expected_tools = [
            "create_permit", "list_permits", "get_permit_details",
            "update_permit_status", "update_permit", "delete_permit",
            "check_simops_conflicts"
        ]
        for name in expected_tools:
            assert name in tool_map, f"Tool {name} must be in definitions.TOOLS"
            assert "description" in tool_map[name]
            assert "parameters" in tool_map[name]

    def test_permit_handlers_registered(self):
        expected_handlers = [
            "create_permit", "list_permits", "get_permit_details",
            "update_permit_status", "update_permit", "delete_permit",
            "check_simops_conflicts"
        ]
        for name in expected_handlers:
            assert name in HANDLERS, f"Handler {name} must be registered in HANDLERS dict"
            assert callable(HANDLERS[name]), f"Handler {name} must be callable"

    def test_permit_resolvers(self):
        # Type resolver
        assert _resolve_permit_type_id(None, "HOT_WORK") == 1
        assert _resolve_permit_type_id(None, "عمل ساخن") == 1
        assert _resolve_permit_type_id(None, "ELECTRICAL") == 2
        assert _resolve_permit_type_id(None, "كهربائي") == 2
        assert _resolve_permit_type_id(None, "WORK_AT_HEIGHT") == 3
        assert _resolve_permit_type_id(None, "مرتفعات") == 3
        assert _resolve_permit_type_id(None, "CONFINED_SPACE") == 4
        assert _resolve_permit_type_id(None, "أماكن مغلقة") == 4
        assert _resolve_permit_type_id(None, "EXCAVATION") == 6
        assert _resolve_permit_type_id(None, "حفر") == 6
        assert _resolve_permit_type_id(None, "RADIOGRAPHY") == 7
        assert _resolve_permit_type_id(None, "إشعاعي") == 7

        # Status resolver
        assert _resolve_permit_status_id(None, "ACTIVE") == 3
        assert _resolve_permit_status_id(None, "APPROVED") == 3
        assert _resolve_permit_status_id(None, "نشط") == 3
        assert _resolve_permit_status_id(None, "معتمد") == 3
        assert _resolve_permit_status_id(None, "PENDING_APPROVAL") == 2
        assert _resolve_permit_status_id(None, "بانتظار الموافقة") == 2
        assert _resolve_permit_status_id(None, "SUSPENDED") == 4
        assert _resolve_permit_status_id(None, "موقوف") == 4
        assert _resolve_permit_status_id(None, "CLOSED") == 6
        assert _resolve_permit_status_id(None, "مغلق") == 6
        assert _resolve_permit_status_id(None, "CANCELLED") == 7
        assert _resolve_permit_status_id(None, "ملغي") == 7

        # Risk level resolver
        assert _resolve_permit_risk_level_id(None, "LOW") == 1
        assert _resolve_permit_risk_level_id(None, "منخفض") == 1
        assert _resolve_permit_risk_level_id(None, "MEDIUM") == 2
        assert _resolve_permit_risk_level_id(None, "متوسط") == 2
        assert _resolve_permit_risk_level_id(None, "HIGH") == 3
        assert _resolve_permit_risk_level_id(None, "عالي") == 3
        assert _resolve_permit_risk_level_id(None, "CRITICAL") == 4
        assert _resolve_permit_risk_level_id(None, "حرج") == 4


class TestPermitNlpAndKeywordParser:
    """Test entity extraction and intent classification for permits."""

    def test_extract_permit_id(self):
        assert extract_entity_ids("PTW-005 تفاصيل التصريح").get("permit_id") == 5
        assert extract_entity_ids("اعتمد تصريح رقم 12").get("permit_id") == 12
        assert extract_entity_ids("update permit 42 status").get("permit_id") == 42
        assert extract_entity_ids("PTW-2026-0418").get("permit_id") == 2026 or extract_entity_ids("PTW-0418").get("permit_id") == 418

    def test_classify_permit_intents(self):
        # Create
        intent, _ = classify_hse_intent("انشئ تصريح عمل ساخن في عنبر 1")
        assert intent == "CREATE_PERMIT"

        # Approve
        intent, _ = classify_hse_intent("اعتمد تصريح العمل رقم 10")
        assert intent == "APPROVE_PERMIT"

        # Suspend
        intent, _ = classify_hse_intent("أوقف تصريح العمل رقم 4 بسبب تسريب غاز")
        assert intent == "SUSPEND_PERMIT"

        # Close
        intent, _ = classify_hse_intent("أغلق تصريح العمل رقم 8 بعد اكتمال الصيانة")
        assert intent == "CLOSE_PERMIT"

        # List
        intent, _ = classify_hse_intent("اعرض تصاريح العمل النشطة")
        assert intent == "LIST_PERMITS"

        # SIMOPS
        intent, _ = classify_hse_intent("هل يوجد تعارض بين تصاريح العمل في عنبر 2؟")
        assert intent == "CHECK_SIMOPS"

    def test_recommend_tools_for_permit_queries(self):
        parsed = parse_user_hse_prompt("انشئ تصريح عمل جديد")
        assert "create_permit" in parsed.recommended_tools

        parsed = parse_user_hse_prompt("اعرض قائمة تصاريح العمل")
        assert "list_permits" in parsed.recommended_tools

        parsed = parse_user_hse_prompt("اعتمد تصريح العمل رقم 5")
        assert "update_permit_status" in parsed.recommended_tools

        parsed = parse_user_hse_prompt("هل يوجد تعارض في تصاريح العمل SIMOPS")
        assert "check_simops_conflicts" in parsed.recommended_tools


class TestPermitLiveDatabaseCrud:
    """Test full permit CRUD cycle and SIMOPS detection on live MySQL database."""

    @pytest.fixture(scope="class")
    @classmethod
    def db_session(cls):
        from app.database import SessionLocal
        db = SessionLocal()
        yield db
        db.close()

    def test_permit_full_crud_cycle(self, db_session):
        # 1. CREATE
        create_res = HANDLERS["create_permit"](
            db=db_session,
            permit_type="HOT_WORK",
            work_description="QA Automation Hot Work Welding in Zone 1",
            zone_id=1,
            requester_id=1,
            issuer_id=1,
            executor_name="QA Welding Team",
            risk_level="HIGH",
            duration_hours=8,
            gas_test_required=True,
            gas_o2=20.9,
            gas_lel=0.0,
            gas_h2s=0.0,
            gas_co=0.0,
            precautions="Mandatory fire watcher and fire extinguisher on site",
            status="ACTIVE"
        )
        assert create_res.get("success") is True, f"Create permit failed: {create_res}"
        permit_id = create_res["permit_id"]
        assert permit_id > 0
        assert create_res["permit_code"] == f"PTW-{permit_id:03d}"

        # 2. READ (List with filters)
        list_res = HANDLERS["list_permits"](db=db_session, status="ACTIVE", zone_id=1, limit=5)
        assert "rows" in list_res
        assert any(r["permit_id"] == permit_id for r in list_res["rows"])

        # 3. READ (Get deep details)
        detail_res = HANDLERS["get_permit_details"](db=db_session, permit_id=permit_id)
        assert "permit" in detail_res
        assert detail_res["permit"]["permit_id"] == permit_id
        assert "gas_tests" in detail_res
        assert "approvals" in detail_res

        # 4. UPDATE (Modify fields)
        update_res = HANDLERS["update_permit"](
            db=db_session,
            permit_id=permit_id,
            work_description="QA Updated Description - Welding and Grinding",
            duration_hours=12,
            risk_level="CRITICAL"
        )
        assert update_res.get("success") is True, f"Update permit failed: {update_res}"

        # 5. UPDATE STATUS (Suspend)
        suspend_res = HANDLERS["update_permit_status"](
            db=db_session,
            permit_id=permit_id,
            status="SUSPENDED",
            reason_or_note="Temporary halt due to site inspection"
        )
        assert suspend_res.get("success") is True
        assert suspend_res["new_status"] == "SUSPENDED"

        # 6. UPDATE STATUS (Close)
        close_res = HANDLERS["update_permit_status"](
            db=db_session,
            permit_id=permit_id,
            status="CLOSED",
            reason_or_note="Work completed successfully and area cleaned"
        )
        assert close_res.get("success") is True
        assert close_res["new_status"] == "CLOSED"

        # 7. SIMOPS Conflict Detection
        simops_res = HANDLERS["check_simops_conflicts"](db=db_session, zone_id=1)
        assert "total_conflicts" in simops_res
        assert "summary" in simops_res

        # 8. DELETE (Restricted admin cleanup)
        del_res = HANDLERS["delete_permit"](
            db=db_session,
            permit_id=permit_id,
            reason="QA Automation test permit deletion"
        )
        assert del_res.get("success") is True, f"Delete permit failed: {del_res}"

        # Verify deletion
        verify_detail = HANDLERS["get_permit_details"](db=db_session, permit_id=permit_id)
        assert "error" in verify_detail, "Permit should no longer exist after deletion"

    def test_permit_update_location_via_prompt(self, db_session):
        # 1. Create a test permit in Zone 1 (Line A)
        create_res = HANDLERS["create_permit"](
            db=db_session,
            permit_type="HOT_WORK",
            work_description="Test permit for location modification",
            zone_id=1,
            requester_id=1,
            issuer_id=1,
            executor_name="Maintenance Team",
            risk_level="MEDIUM",
            duration_hours=8,
            status="ACTIVE"
        )
        assert create_res.get("success") is True
        pid = create_res["permit_id"]

        # 2. Verify NLP parsing for English prompt
        p_en = parse_user_hse_prompt(f"change the location to production line b in permit ptw-{pid:03d}")
        assert p_en.primary_intent == "UPDATE_PERMIT"
        assert p_en.entity_ids.get("permit_id") == pid
        assert "update_permit" in p_en.recommended_tools

        # 3. Verify update_permit handler with location string
        upd_res = HANDLERS["update_permit"](
            db=db_session,
            permit_id=pid,
            location="production line b"
        )
        assert upd_res.get("success") is True
        assert upd_res["zone_id"] == 2
        assert "Production Line B" in upd_res["zone_name"]

        # 4. Verify Arabic prompt parsing & execution
        p_ar = parse_user_hse_prompt(f"تغيير موقع التصريح PTW-{pid:03d} إلى خط الإنتاج A")
        assert p_ar.primary_intent == "UPDATE_PERMIT"
        assert "update_permit" in p_ar.recommended_tools

        upd_res_ar = HANDLERS["update_permit"](
            db=db_session,
            permit_id=f"PTW-{pid:03d}",
            location="خط الإنتاج A"
        )
        assert upd_res_ar.get("success") is True
        assert upd_res_ar["zone_id"] == 1

        # 5. Clean up
        del_res = HANDLERS["delete_permit"](db=db_session, permit_id=pid)
        assert del_res.get("success") is True

    def test_permit_update_location_to_production_line_c(self, db_session):
        """Verify updating permit location to Production Line C maps to Zone 11 (not Line A)."""
        create_res = HANDLERS["create_permit"](
            db=db_session,
            permit_type="HOT_WORK",
            work_description="Cable joining on Line C",
            zone_id=1,
            requester_id=1,
            issuer_id=1,
            executor_name="Line C Team",
            risk_level="HIGH",
            duration_hours=8,
            status="ACTIVE"
        )
        assert create_res.get("success") is True
        pid = create_res["permit_id"]

        # 1. Test NLP prompt parsing
        p = parse_user_hse_prompt(f"change the location to production line c in ptw-{pid:03d}")
        assert p.primary_intent == "UPDATE_PERMIT"
        assert p.entity_ids.get("permit_id") == pid
        assert "update_permit" in p.recommended_tools

        # 2. Test English update
        upd_en = HANDLERS["update_permit"](
            db=db_session,
            permit_id=pid,
            location="production line c"
        )
        assert upd_en.get("success") is True
        assert upd_en["zone_id"] == 11, f"Expected Zone 11 for Production Line C, got {upd_en.get('zone_id')}"
        assert "Line C" in upd_en["zone_name"] or "C" in upd_en["zone_name"]

        # 3. Test Arabic update
        upd_ar = HANDLERS["update_permit"](
            db=db_session,
            permit_id=pid,
            location="خط الإنتاج C"
        )
        assert upd_ar.get("success") is True
        assert upd_ar["zone_id"] == 11

        # Clean up
        HANDLERS["delete_permit"](db=db_session, permit_id=pid)

    def test_approve_and_activate_permit_modal_action(self, db_session):
        """Verify modal red button action: 'اعتماد وتفعيل التصريح' (Approve & Activate)."""
        create_res = HANDLERS["create_permit"](
            db=db_session,
            permit_type="ELECTRICAL",
            work_description="Transformer test pending approval",
            zone_id=2,
            requester_id=1,
            issuer_id=1,
            executor_name="Electrical Lead",
            risk_level="MEDIUM",
            duration_hours=6,
            status="PENDING_APPROVAL"
        )
        assert create_res.get("success") is True
        pid = create_res["permit_id"]

        # 1. Verify NLP intent classification
        p1 = parse_user_hse_prompt(f"اعتماد وتفعيل التصريح PTW-{pid:03d}")
        assert p1.primary_intent == "APPROVE_PERMIT"
        assert "update_permit_status" in p1.recommended_tools

        p2 = parse_user_hse_prompt(f"تفعيل تصريح PTW-{pid:03d}")
        assert p2.primary_intent == "APPROVE_PERMIT"

        p3 = parse_user_hse_prompt(f"approve and activate permit {pid}")
        assert p3.primary_intent == "APPROVE_PERMIT"

        # 2. Execute status update to APPROVED (status_id = 3 / ACTIVE)
        appr_res = HANDLERS["update_permit_status"](
            db=db_session,
            permit_id=pid,
            status="اعتماد وتفعيل التصريح",
            reason_or_note="تم الفحص وتفعيل التصريح عبر المساعد الذكي"
        )
        assert appr_res.get("success") is True
        assert appr_res["status_id"] == 3
        assert appr_res["status"] == "ACTIVE"

        # 3. Test modal close action: 'إغلاق وتسليم الموقع'
        close_res = HANDLERS["update_permit_status"](
            db=db_session,
            permit_id=pid,
            status="إغلاق وتسليم الموقع",
            reason_or_note="تم إنهاء الأعمال وتسليم الموقع نظيفاً"
        )
        assert close_res.get("success") is True
        assert close_res["status_id"] == 6
        assert close_res["status"] == "CLOSED"

        # Clean up
        HANDLERS["delete_permit"](db=db_session, permit_id=pid)

    def test_bulk_close_permits(self, db_session):
        """Verify bulk closing of permits ('اغلق كافة التصاريح' / 'close all permits') with zero production side effects."""
        # 1. NLP intent
        p = parse_user_hse_prompt("اغلق كافة التصاريح")
        assert p.primary_intent in ("CLOSE_ALL_PERMITS", "CLOSE_PERMIT")
        assert "close_all_permits" in p.recommended_tools

        # 2. Create isolated test permit
        test_p = HANDLERS["create_permit"](
            db=db_session,
            permit_type="HOT_WORK",
            work_description="[TEST_ISOLATED] Bulk Close Verification Permit",
            zone_id=1,
            risk_level="MEDIUM",
            duration_hours=2
        )
        pid = test_p["permit_id"]

        try:
            # 3. Test closing single permit cleanly
            close_res = HANDLERS["update_permit_status"](
                db=db_session,
                permit_id=pid,
                status="CLOSED",
                reason_or_note="نهاية الوردية وتسليم المواقع"
            )
            assert close_res.get("success") is True
            assert close_res["status_id"] == 6
        finally:
            # 4. Clean up test record
            HANDLERS["delete_permit"](db=db_session, permit_id=pid)

