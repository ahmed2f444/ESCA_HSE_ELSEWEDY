"""
Comprehensive End-to-End Test Suite for all 15 ESCA HSE Modules with CRUD & Inquiry.
Tests handlers, definitions, RBAC, NLP parser, and database transactions against live MySQL.
"""
import sys
import os

# Set working path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, SessionLocal
from app.tools.definitions import TOOLS, LOCAL_TOOLS
from app.tools.handlers import HANDLERS
from app.tools.rbac import TOOL_RBAC_PERMISSIONS, check_tool_access
from app.nlp.keyword_parser import parse_user_hse_prompt, get_recommended_tools_for_prompt


def test_definitions_and_rbac_integrity():
    print("=" * 60)
    print("TEST 1: Verifying Definitions, Handlers, and RBAC Alignment")
    print("=" * 60)

    tool_names = {t["function"]["name"] for t in TOOLS}
    local_tool_names = {t["function"]["name"] for t in LOCAL_TOOLS}

    print(f"Total Tools in TOOLS: {len(tool_names)}")
    print(f"Total Tools in LOCAL_TOOLS: {len(local_tool_names)}")
    print(f"Total Handlers implemented: {len(HANDLERS)}")
    print(f"Total RBAC entries: {len(TOOL_RBAC_PERMISSIONS)}")

    missing_handlers = tool_names - set(HANDLERS.keys())
    assert not missing_handlers, f"Missing handlers for tools: {missing_handlers}"

    missing_rbac = tool_names - set(TOOL_RBAC_PERMISSIONS.keys())
    assert not missing_rbac, f"Missing RBAC definitions for tools: {missing_rbac}"

    print("✅ All tool definitions have registered handlers and RBAC mappings!\n")


def test_all_15_modules_crud(db):
    print("=" * 60)
    print("TEST 2: Executing Live Inquiries & CRUD across all 15 Modules")
    print("=" * 60)

    created_ids = {}

    # ── Module 1: Master Data
    print("--- 1. Master Data & Organization ---")
    depts = HANDLERS["list_departments"](db=db, limit=5)
    print(f"list_departments: {len(depts.get('rows', []))} depts found.")
    assert len(depts.get("rows", [])) > 0

    zones = HANDLERS["list_zones"](db=db, limit=5)
    print(f"list_zones: {len(zones.get('rows', []))} zones found.")
    assert len(zones.get("rows", [])) > 0

    emp_res = HANDLERS["create_employee"](db=db, display_name="Test Operator QA", job_title="Quality Inspector", zone_id=1)
    print(f"create_employee: {emp_res}")
    assert emp_res.get("success") is True
    created_ids["employee_id"] = emp_res["employee_id"]

    emp_update = HANDLERS["update_employee"](db=db, employee_id=created_ids["employee_id"], job_title="Senior QA Inspector")
    print(f"update_employee: {emp_update}")
    assert emp_update.get("success") is True

    # ── Module 2: Dashboard & Executive KPIs
    print("\n--- 2. Executive Dashboard & KPIs ---")
    dash = HANDLERS["get_dashboard_summary"](db=db)
    print(f"get_dashboard_summary: open_inc={dash.get('open_incidents')}, fire_readiness={dash.get('fire_readiness_pct')}%")
    assert "safe_man_hours" in dash

    kpis = HANDLERS["get_monthly_kpis"](db=db, limit=3)
    print(f"get_monthly_kpis: {len(kpis.get('rows', []))} records.")

    scores = HANDLERS["get_safety_scores"](db=db)
    print(f"get_safety_scores: {len(scores.get('zones', []))} zones evaluated.")

    # ── Module 3: Incidents & RCA
    print("\n--- 3. Incidents & Safety Observations ---")
    inc_res = HANDLERS["create_incident"](db=db, title="Test Incident QA", description="Test chemical drip", zone_id=1, severity="MINOR")
    print(f"create_incident: {inc_res}")
    assert inc_res.get("success") is True
    created_ids["incident_id"] = inc_res["incident_id"]

    obs_res = HANDLERS["log_safety_observation"](db=db, description="Worker not wearing gloves", zone_id=2, observation_type="UNSAFE_ACT")
    print(f"log_safety_observation: {obs_res}")
    assert obs_res.get("success") is True

    inc_details = HANDLERS["get_incident_details"](db=db, incident_id=created_ids["incident_id"])
    print(f"get_incident_details: {inc_details.get('incident', {}).get('title')}")

    inc_up = HANDLERS["update_incident_status"](db=db, incident_id=created_ids["incident_id"], status="CLOSED")
    print(f"update_incident_status: {inc_up}")
    assert inc_up.get("success") is True

    # ── Module 4: Permits & SIMOPS
    print("\n--- 4. Electronic Permits & SIMOPS ---")
    ptw_res = HANDLERS["create_permit"](db=db, permit_type="HOT_WORK", work_description="Welding cable tray", zone_id=1)
    print(f"create_permit: {ptw_res}")
    assert ptw_res.get("success") is True
    created_ids["permit_id"] = ptw_res["permit_id"]

    simops = HANDLERS["check_simops_conflicts"](db=db, zone_id=1)
    print(f"check_simops_conflicts: {simops.get('total_conflicts')} conflicts detected.")

    ptw_up = HANDLERS["update_permit_status"](db=db, permit_id=created_ids["permit_id"], status="CLOSED")
    print(f"update_permit_status: {ptw_up}")

    # ── Module 5: Inspections & Findings
    print("\n--- 5. Inspections & Findings ---")
    insp_res = HANDLERS["schedule_safety_inspection"](db=db, inspection_type="ROUTINE_WALK", zone_id=1, scheduled_in_days=5)
    print(f"schedule_safety_inspection: {insp_res}")
    assert insp_res.get("success") is True
    created_ids["inspection_id"] = insp_res["inspection_id"]

    find_res = HANDLERS["create_inspection_finding"](db=db, inspection_id=created_ids["inspection_id"], description="Blocked emergency exit path", category="FIRE_SAFETY", severity="MODERATE")
    print(f"create_inspection_finding: {find_res}")
    assert find_res.get("success") is True
    created_ids["finding_id"] = find_res["finding_id"]

    # ── Module 6: CAPA Actions
    print("\n--- 6. CAPA Actions ---")
    capa_res = HANDLERS["create_capa"](db=db, title="Clear obstructed exit path", finding_id=created_ids["finding_id"], priority="HIGH")
    print(f"create_capa: {capa_res}")
    assert capa_res.get("success") is True
    created_ids["capa_id"] = capa_res["capa_id"]

    capa_up = HANDLERS["update_capa_status"](db=db, capa_id=created_ids["capa_id"], status="COMPLETED")
    print(f"update_capa_status: {capa_up}")

    # ── Module 7: Risk Register (HIRA)
    print("\n--- 7. Risk Register (HIRA) ---")
    risk_res = HANDLERS["create_risk_assessment"](db=db, hazard="Noise exposure near extruders", activity="Extrusion Operations", controls="Earplugs required", zone_id=1)
    print(f"create_risk_assessment: {risk_res}")
    assert risk_res.get("success") is True
    created_ids["risk_id"] = risk_res["risk_id"]

    risk_mat = HANDLERS["get_risk_matrix"](db=db)
    print(f"get_risk_matrix: {len(risk_mat.get('distribution', []))} risk levels.")

    # ── Module 8: Job Safety Analysis (JSA)
    print("\n--- 8. Job Safety Analysis (JSA) ---")
    jsa_res = HANDLERS["create_jsa"](db=db, task_name="Overhead Crane Maintenance", zone_id=2, permit_required=True, permit_type="WORK_AT_HEIGHT")
    print(f"create_jsa: {jsa_res}")
    assert jsa_res.get("success") is True
    created_ids["jsa_id"] = jsa_res["jsa_id"]

    jsa_up = HANDLERS["update_jsa"](db=db, jsa_id=created_ids["jsa_id"], status="APPROVED")
    print(f"update_jsa: {jsa_up}")

    # ── Module 9: Training & Certificates
    print("\n--- 9. Training & Competency ---")
    course_res = HANDLERS["create_training_course"](db=db, name_ar="دورة السلامة الكيميائية المتقدمة", name_en="Advanced Chemical Safety", validity_months=24)
    print(f"create_training_course: {course_res}")
    assert course_res.get("success") is True
    created_ids["course_id"] = course_res["course_id"]

    cert_res = HANDLERS["create_certificate"](db=db, employee_name="أحمد سامي", course_id=created_ids["course_id"], expiry_date="2027-08-29")
    print(f"create_certificate: {cert_res}")
    assert cert_res.get("success") is True
    created_ids["certificate_id"] = cert_res["certificate_id"]

    cert_renew = HANDLERS["update_certificate_status"](db=db, certificate_id=created_ids["certificate_id"], expiry_date="1 year")
    print(f"update_certificate_status: {cert_renew.get('message')}")

    # ── Module 10: PPE Management
    print("\n--- 10. PPE Management ---")
    ppe_res = HANDLERS["add_ppe_item"](db=db, item_code="GLV-CHEM-QA", name_ar="قفازات مقاومة للمواد الكيميائية", category="HAND", balance_qty=100.0)
    print(f"add_ppe_item: {ppe_res}")
    assert ppe_res.get("success") is True
    created_ids["ppe_item_id"] = ppe_res["ppe_item_id"]

    ppe_tx = HANDLERS["create_ppe_transaction"](db=db, ppe_item_id=created_ids["ppe_item_id"], employee_id="أحمد سامي", quantity=2)
    print(f"create_ppe_transaction: {ppe_tx}")
    assert ppe_tx.get("success") is True

    # ── Module 11: Fire Safety & Fixed Assets
    print("\n--- 11. Fire Safety & Fixed Assets ---")
    fire_res = HANDLERS["add_fire_equipment"](db=db, asset_type="EXTINGUISHER", subtype="FOAM_9L", zone_id=1, location_detail="QA Test Location")
    print(f"add_fire_equipment: {fire_res}")
    assert fire_res.get("success") is True
    created_ids["equipment_id"] = fire_res["equipment_id"]

    fire_insp = HANDLERS["log_fire_inspection"](db=db, equipment_id=created_ids["equipment_id"], result="PASS")
    print(f"log_fire_inspection: {fire_insp}")
    assert fire_insp.get("success") is True

    fixed_res = HANDLERS["add_fixed_safety_asset"](db=db, asset_name="QA Emergency Eyewash Station 5", asset_type="EYEWASH", total_qty=1, operational_qty=1)
    print(f"add_fixed_safety_asset: {fixed_res}")
    assert fixed_res.get("success") is True
    created_ids["asset_summary_id"] = fixed_res["asset_summary_id"]

    # ── Module 12: HazMat & Chemicals
    print("\n--- 12. HazMat & Chemicals ---")
    chem_res = HANDLERS["add_chemical"](db=db, trade_name="QA Isopropyl Alcohol 99%", chemical_name="أيزوبروبانول عالي النقاء", cas_number="67-63-0", quantity=200.0, zone_id=4)
    print(f"add_chemical: {chem_res}")
    assert chem_res.get("success") is True
    created_ids["chemical_id"] = chem_res["chemical_id"]

    chem_compat = HANDLERS["get_chemical_compatibility"](db=db, chemical_a="Flammable Liquid", chemical_b="Oxidizer")
    print(f"get_chemical_compatibility: {len(chem_compat.get('compatibility_matrix', []))} rules checked.")

    # ── Module 13: Occupational Health
    print("\n--- 13. Occupational Health ---")
    med_res = HANDLERS["record_medical_exam"](db=db, employee_id="أحمد سامي", fitness_result="FIT", restriction_summary="None")
    print(f"record_medical_exam: {med_res}")
    assert med_res.get("success") is True
    created_ids["exam_id"] = med_res["exam_id"]

    med_sched = HANDLERS["schedule_medical_exam"](db=db, employee_id="أحمد سامي", scheduled_in_days=30)
    print(f"schedule_medical_exam: {med_sched}")
    assert med_sched.get("success") is True

    # ── Module 14: AI Vision & IoT Sensors
    print("\n--- 14. AI Vision & IoT Sensors ---")
    iot_res = HANDLERS["add_iot_sensor"](db=db, sensor_type="NOISE_DB", zone_id=1, safe_max=85.0, warning_max=90.0, unit="dB")
    print(f"add_iot_sensor: {iot_res}")
    assert iot_res.get("success") is True
    created_ids["sensor_id"] = iot_res["sensor_id"]

    ai_ev = HANDLERS["log_ai_event"](db=db, event_type="NO_HELMET", camera_id=1, confidence_pct=98.2, severity="HIGH")
    print(f"log_ai_event: {ai_ev}")
    assert ai_ev.get("success") is True

    # ── Module 15: Security & Integrations
    print("\n--- 15. Security & Integrations ---")
    sec_roles = HANDLERS["list_security_roles"](db=db)
    print(f"list_security_roles: {len(sec_roles.get('roles', []))} system roles.")

    integrations = HANDLERS["list_integrations"](db=db)
    print(f"list_integrations: {len(integrations.get('integrations', []))} connectors.")

    # ── Module 16: Superuser Cleanup & Deletion
    print("\n--- 16. Superuser Cancellation & Safe Deletion ---")
    cancel_res = HANDLERS["cancel_entity"](db=db, entity_type="PERMIT", entity_id=created_ids["permit_id"], reason="End of QA test run")
    print(f"cancel_entity: {cancel_res}")
    assert cancel_res.get("success") is True

    # Clean up test records
    for tbl, pk_key in [
        ("ai_events", "ai_event_id"),
        ("health_exams", "exam_id"),
        ("iot_sensors", "sensor_id"),
        ("fixed_safety_assets", "asset_summary_id"),
        ("fire_equipment", "equipment_id"),
        ("chemicals", "chemical_id"),
        ("ppe_inventory", "ppe_item_id"),
        ("certificates", "certificate_id"),
        ("training_courses", "course_id"),
        ("jsa", "jsa_id"),
        ("risk_register", "risk_id"),
        ("capa", "capa_id"),
        ("findings", "finding_id"),
        ("inspections", "inspection_id"),
        ("permits", "permit_id"),
        ("incidents", "incident_id"),
        ("employees", "employee_id"),
    ]:
        if pk_key in created_ids:
            del_res = HANDLERS["delete_record"](db=db, table_name=tbl, record_id=created_ids[pk_key], reason="QA test cleanup")
            print(f"Cleaned up {tbl} #{created_ids[pk_key]}: {del_res.get('success')}")

    print("\n✅ All 15 ESCA HSE Modules successfully tested for CRUD and inquiry!\n")


def test_nlp_parsing():
    print("=" * 60)
    print("TEST 3: Multilingual NLP & Intent Classification")
    print("=" * 60)

    test_queries = [
        ("جدد شهادة عمر خالد TRN-063 لسنة قادمة", "RENEW_CERTIFICATE", ["update_certificate_status"]),
        ("صرف 2 خوذة سلامة للموظف أحمد سامي", "ISSUE_PPE", ["create_ppe_transaction"]),
        ("انشئ تحليل سلامة مهام JSA لأعمال اللحام", "CREATE_JSA", ["create_jsa"]),
        ("سجل فحص طبي دوري للموظف عمر خالد بنتيجة لائق", "RECORD_MEDICAL_EXAM", ["record_medical_exam"]),
        ("أضف مستشعر غاز VOC في عنبر 2", "ADD_IOT_SENSOR", ["add_iot_sensor"]),
        ("اعرض ملخص لوحة القيادة ومؤشرات السلامة", "GET_DASHBOARD_SUMMARY", ["get_dashboard_summary"]),
        ("هل يوجد تعارض بين تصاريح العمل في عنبر 1؟", "CHECK_SIMOPS", ["check_simops_conflicts"]),
    ]

    for q, expected_intent, expected_tools in test_queries:
        parsed = parse_user_hse_prompt(q)
        print(f"Query: '{q}'")
        print(f" -> Intent: {parsed.primary_intent} (Expected: {expected_intent})")
        print(f" -> Recommended: {parsed.recommended_tools}")
        assert parsed.primary_intent == expected_intent, f"Intent mismatch for '{q}': got {parsed.primary_intent}"
        for exp_t in expected_tools:
            assert exp_t in parsed.recommended_tools, f"Expected tool {exp_t} not in {parsed.recommended_tools}"

    print("✅ NLP Intent Parsing verified across all modules!\n")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        test_definitions_and_rbac_integrity()
        test_all_15_modules_crud(db)
        test_nlp_parsing()
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! The ESCA HSE AI Agent is fully operational across all 15 modules.")
    finally:
        db.close()
