"""
Integration and Unit Test Suite for Fire Equipment UI Automation
Tests all 8 UI buttons and actions:
1. Field inspection logging ([تسجيل فحص لهذه المعدة], [تسجيل فحص ميداني], [فحص])
2. Unit details & QR modal ([تفاصيل معدة الإطفاء FE-0031])
3. Readiness and compliance reports ([تقرير الجاهزية])
4. Periodic inspection schedule ([جدول الفحص])
5. Service work orders & refill / replacement ([استبدال فوري], [إعادة تعبئة], [أمر شغل])
6. Urgent attention list query ([معدات تحتاج انتباه فوري])
7. Coverage and readiness by zone ([تغطية وجاهزية الشبكة حسب المنطقة])
8. KPI summary statistics
"""

import re
import pytest
from datetime import date, timedelta
from sqlalchemy import text

from app.database import get_db, SessionLocal
from app.tools.rbac import check_tool_access, filter_tools_for_role, ROLE_ADMIN, ROLE_HSE_MANAGER, ROLE_HSE_OFFICER, ROLE_MAINTENANCE_ENGINEER, ROLE_OPERATIONS_MANAGER, ROLE_AUDITOR, ROLE_WORKER
from app.tools.definitions import TOOLS, LOCAL_TOOLS
from app.tools.handlers import (
    HANDLERS,
    _resolve_fire_equipment_id,
    log_fire_inspection,
    service_fire_equipment,
    get_fire_equipment_detail,
    get_fire_readiness_report,
    get_fire_inspection_schedule,
    get_fire_attention_list,
    get_fire_coverage_by_zone,
    get_fire_equipment_stats,
    add_fire_equipment,
    list_fire_equipment,
)
from app.nlp.keyword_parser import (
    classify_hse_intent,
    classify_module_affinity,
    get_recommended_tools_for_prompt,
    extract_all_hse_entities,
)


class TestFireEquipmentRbacPermissions:
    """RBAC validation for all fire safety tools."""

    @pytest.mark.parametrize("tool_name", [
        "log_fire_inspection", "service_fire_equipment", "add_fire_equipment", "update_fire_equipment"
    ])
    def test_admin_and_hse_manager_have_mutation_access(self, tool_name):
        auth_admin, _ = check_tool_access(ROLE_ADMIN, tool_name)
        auth_mgr, _ = check_tool_access(ROLE_HSE_MANAGER, tool_name)
        assert auth_admin is True
        assert auth_mgr is True

    @pytest.mark.parametrize("tool_name", [
        "log_fire_inspection", "service_fire_equipment", "update_fire_equipment"
    ])
    def test_maintenance_engineer_has_service_access(self, tool_name):
        auth, _ = check_tool_access(ROLE_MAINTENANCE_ENGINEER, tool_name)
        assert auth is True

    @pytest.mark.parametrize("tool_name", [
        "get_fire_equipment_detail", "get_fire_equipment_stats"
    ])
    def test_worker_and_auditor_have_read_access(self, tool_name):
        auth_worker, _ = check_tool_access(ROLE_WORKER, tool_name)
        auth_auditor, _ = check_tool_access(ROLE_AUDITOR, tool_name)
        assert auth_worker is True
        assert auth_auditor is True

    def test_worker_cannot_mutate_fire_equipment(self):
        auth, _ = check_tool_access(ROLE_WORKER, "service_fire_equipment")
        assert auth is False
        auth_add, _ = check_tool_access(ROLE_WORKER, "add_fire_equipment")
        assert auth_add is False


class TestFireEquipmentDefinitionsAndHandlers:
    """Tool schema and registry verification."""

    FIRE_TOOLS = [
        "log_fire_inspection",
        "service_fire_equipment",
        "get_fire_equipment_detail",
        "get_fire_readiness_report",
        "get_fire_inspection_schedule",
        "get_fire_attention_list",
        "get_fire_coverage_by_zone",
        "get_fire_equipment_stats",
        "add_fire_equipment",
        "list_fire_equipment",
        "update_fire_equipment",
    ]

    def test_all_fire_tools_in_definitions(self):
        tool_names = [t["function"]["name"] for t in TOOLS if "function" in t]
        for ft in self.FIRE_TOOLS:
            assert ft in tool_names, f"Tool '{ft}' missing from TOOLS definitions"

    def test_all_fire_tools_in_handlers_map(self):
        for ft in self.FIRE_TOOLS:
            assert ft in HANDLERS, f"Handler '{ft}' missing from HANDLERS registry"
            assert callable(HANDLERS[ft]), f"Handler '{ft}' is not callable"


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestFireEquipmentDatabaseAutomation:
    """Live database testing of all 8 button flows."""

    def test_fire_equipment_tag_resolution(self, db):
        eid, tag = _resolve_fire_equipment_id(db, "FE-0031")
        assert tag.startswith("FE-")

        eid4, tag4 = _resolve_fire_equipment_id(db, "FE-0004")
        assert tag4.startswith("FE-")

        eid_num, tag_num = _resolve_fire_equipment_id(db, 4)
        assert eid_num == 4

    def test_button_action_log_fire_inspection(self, db):
        """Simulates clicking [تسجيل فحص لهذه المعدة] on FE-0031 modal."""
        res = log_fire_inspection(
            db=db,
            equipment_id="FE-0031",
            pressure_ok=True,
            hose_ok=True,
            safety_pin_ok=True,
            access_clear=True,
            result="PASS",
            notes="فحص ميداني مطابق - مسح كود QR من داخل نطاق 15م"
        )
        assert res.get("success") is True
        assert res.get("result") == "PASS"
        assert "next_due_date" in res

        # Verify DB updated
        eq_id = res.get("equipment_id")
        row = db.execute(text("SELECT status_id, last_inspection_date FROM fire_equipment WHERE equipment_id = :id"), {"id": eq_id}).fetchone()
        assert row is not None
        assert row[0] == 1  # 1 = VALID

    def test_button_action_service_fire_equipment_replace(self, db):
        """Simulates clicking [استبدال فوري] button in attention table."""
        res = service_fire_equipment(
            db=db,
            equipment_id="FE-0004",
            action_type="REPLACE",
            technician_name="م. حسام الدين (فريق الصيانة المعتمد)",
            recommission_now=True,
        )
        assert res.get("success") is True
        assert res.get("action_type") == "REPLACE"
        assert res.get("work_order_id", "").startswith("WO-")
        assert res.get("status") == "VALID"

        # Expiry should be ~5 years ahead
        exp_year = int(res["new_expiry_date"].split("-")[0])
        assert exp_year >= date.today().year + 4

    def test_button_action_service_fire_equipment_refill(self, db):
        """Simulates clicking [إعادة تعبئة] button in attention table."""
        res = service_fire_equipment(
            db=db,
            equipment_id="FE-0005",
            action_type="REFILL",
            technician_name="م. حسام الدين (فريق الصيانة المعتمد)",
            recommission_now=True,
        )
        assert res.get("success") is True
        assert res.get("action_type") == "REFILL"
        assert res.get("work_order_id", "").startswith("WO-")

        # Expiry should be ~2 years ahead
        exp_year = int(res["new_expiry_date"].split("-")[0])
        assert exp_year >= date.today().year + 1

    def test_button_action_get_fire_equipment_detail_modal(self, db):
        """Simulates opening unit card modal [تفاصيل معدة الإطفاء FE-0031]."""
        res = get_fire_equipment_detail(db=db, equipment_id="FE-0031")
        assert res.get("success") is True
        assert "qr_code" in res
        assert "location_detail" in res
        assert "compliance_note" in res
        assert "recent_inspections" in res
        assert "status_label_ar" in res

    def test_button_action_get_fire_readiness_report(self, db):
        """Simulates clicking [تقرير الجاهزية] button."""
        res = get_fire_readiness_report(db=db)
        assert res.get("success") is True
        assert "readiness_percentage" in res
        assert "summary_kpis" in res
        assert res["summary_kpis"]["fire_hydrants_count"] == 24
        assert res["summary_kpis"]["smoke_detectors_total"] == 64
        assert "zone_breakdown" in res
        assert "standards_compliance" in res

    def test_button_action_get_fire_inspection_schedule(self, db):
        """Simulates clicking [جدول الفحص] button."""
        res = get_fire_inspection_schedule(db=db)
        assert res.get("success") is True
        assert "15" in res.get("cycle_frequency", "")
        assert "upcoming_inspections_due" in res
        assert "inspection_protocols" in res

    def test_button_action_get_fire_attention_list(self, db):
        """Simulates fetching [معدات تحتاج انتباه فوري] table data."""
        res = get_fire_attention_list(db=db, limit=10)
        assert res.get("success") is True
        assert isinstance(res.get("rows"), list)

    def test_button_action_get_fire_coverage_by_zone(self, db):
        """Simulates fetching [تغطية وجاهزية الشبكة حسب المنطقة] table data."""
        res = get_fire_coverage_by_zone(db=db)
        assert res.get("success") is True
        assert len(res.get("rows", [])) > 0
        assert "pct" in res["rows"][0]

    def test_button_action_get_fire_equipment_stats(self, db):
        """Simulates reading KPI tiles."""
        res = get_fire_equipment_stats(db=db)
        assert res.get("success") is True
        assert "total" in res
        assert "serviceable" in res
        assert res["hydrants"] == 24
        assert res["smoke_detectors"] == 64


class TestFireEquipmentNlpIntents:
    """Multilingual Arabic & English intent recognition."""

    @pytest.mark.parametrize("prompt,expected_intent", [
        ("سجل فحص ميداني لمعدة الإطفاء FE-0031", "LOG_FIRE_INSPECTION"),
        ("تسجيل فحص لهذه المعدة FE-0031", "LOG_FIRE_INSPECTION"),
        ("استبدال فوري لطفاية الحريق FE-0004", "SERVICE_FIRE_EQUIPMENT"),
        ("إعادة تعبئة طفاية الحريق FE-0005", "SERVICE_FIRE_EQUIPMENT"),
        ("أمر شغل صيانة لطفاية FE-0006", "SERVICE_FIRE_EQUIPMENT"),
        ("اعرض تقرير الجاهزية لشبكة الإطفاء", "GET_FIRE_READINESS_REPORT"),
        ("تصدير تقرير جاهزية معدات الحريق", "GET_FIRE_READINESS_REPORT"),
        ("اعرض جدول الفحص الدوري لمعدات الإطفاء", "GET_FIRE_INSPECTION_SCHEDULE"),
        ("تفاصيل معدة الإطفاء FE-0031 وكود المسح", "GET_FIRE_EQUIPMENT_DETAIL"),
        ("ما هي معدات الحريق التي تحتاج انتباه فوري؟", "GET_FIRE_ATTENTION_LIST"),
        ("تغطية وجاهزية الشبكة حسب المنطقة", "GET_FIRE_COVERAGE_BY_ZONE"),
        ("ما هي إحصائيات معدات الحريق وكواشف الدخان؟", "GET_FIRE_EQUIPMENT_STATS"),
    ])
    def test_fire_safety_intent_classification(self, prompt, expected_intent):
        primary_intent, all_intents = classify_hse_intent(prompt)
        module_affinities = classify_module_affinity(prompt)
        module_ids = [m["module_id"] for m in module_affinities]
        assert 11 in module_ids, f"Module 11 (Fire Safety) should be triggered for prompt: '{prompt}' (got {module_ids})"
        assert expected_intent in all_intents or primary_intent == expected_intent, f"Intent '{expected_intent}' not found in: primary={primary_intent}, all={all_intents}"

    def test_entity_extractor_finds_fe_tag(self):
        entities = extract_all_hse_entities("سجل فحص لطفاية FE-0031 بالموقع")
        assert entities.get("equipment_id") == 31 or entities.get("raw_ids", {}).get("equipment_id") == 31
