"""
Comprehensive Automated Test Suite for Inspections & Safety Walks AI Agent Actions
Verifies all 6 UI button actions and workflows on /inspections:
1. Schedule Walk (جدولة جولة): recurrence, inspector, date, template, notes, zone.
2. Submit Live Walk (بدء جولة تفتيش): type, score %, checklist Pass/Fail, auto findings & CAPAs.
3. Inspection Assistant Stats & Recommendations (مساعد التفتيش الذكي AI): stats, compliance %.
4. Mobile QR Inspection Simulation (محاكاة مسح الكود): equipment tags (QR-FE-A-014), checklist booleans, pass/fail result.
5. Findings Management (ملاحظات عدم المطابقة): creation, listing, closing status, CAPA linking.
6. Form Builder & Standards (بانى نماذج التفتيش): ISO 45001, ISO 14001, OSHA 1910, NFPA, BBS, 5S.
7. NLP Keyword Extraction & Routing: Arabic & English phrasing.
"""
import pytest
from app.database import SessionLocal
from app.tools.handlers import (
    schedule_safety_inspection,
    submit_inspection_walk,
    list_inspections,
    get_inspection_details,
    get_inspection_stats,
    update_inspection_status,
    update_inspection,
    delete_inspection,
    create_inspection_finding,
    list_inspection_findings,
    update_inspection_finding,
    delete_inspection_finding,
    list_inspection_templates,
    generate_inspection_checklist,
    log_fire_inspection,
)
from app.nlp.keyword_parser import parse_user_hse_prompt, extract_entity_ids


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_schedule_safety_inspection_modal_fields(db):
    """1. Test Schedule Walk (جدولة جولة) with recurrence, inspector, template, and notes."""
    res = schedule_safety_inspection(
        db=db,
        inspection_type="تفتيش السلامة الأسبوعي لمصنع الكابلات",
        zone_id="خطوط العزل CCV",
        lead_inspector_id="م. مصطفى",
        frequency="أسبوعي",
        scheduled_at="2026-08-31",
        template="ISO 45001 — تدقيق السلامة والصحة المهنية",
        notes="فحص شامل لخطوط الإنتاج والتأكد من توافر مهمات الوقاية"
    )
    assert res.get("success") is True
    assert res.get("inspection_id") is not None
    assert res.get("frequency") == "أسبوعي"
    assert "2026-08-31" in str(res.get("scheduled_at"))
    assert res.get("template") == "ISO 45001 — تدقيق السلامة والصحة المهنية"

    # Verify details
    iid = res["inspection_id"]
    detail = get_inspection_details(db, inspection_id=iid)
    assert not detail.get("error")
    assert detail["inspection"]["inspection_id"] == iid
    assert "ZONE:" in detail["inspection"]["notes"]
    assert "OWNER:" in detail["inspection"]["notes"]


def test_submit_inspection_walk_live_scoring(db):
    """2. Test Submit Live Walk (بدء جولة تفتيش) with checklist scoring and auto CAPAs."""
    checklist_items = [
        {"text": "مسارات الهروب وأبواب الطوارئ خالية تماماً", "status": "PASS"},
        {"text": "التزام جميع العاملين بمهمات الوقاية", "status": "PASS"},
        {"text": "سريان تصاريح العمل الساخنة", "status": "PASS"},
        {"text": "حواجز الأمان على ماكينات السحب", "status": "FAIL"},  # Should generate finding
        {"text": "تأريض اللوحات الكهربائية", "status": "PASS"},
    ]
    res = submit_inspection_walk(
        db=db,
        inspection_type="تفتيش السلامة الميداني الشامل",
        zone_id=1,
        lead_inspector_id="م. مصطفى",
        checklist_version="ISO 45001 — تدقيق السلامة والصحة المهنية",
        checklist=checklist_items,
        notes="تم استكمال التفتيش ورصد عطل بحاجز ماكينة السحب"
    )
    assert res.get("success") is True
    assert res.get("inspection_id") is not None
    # 4 passed out of 5 = 80.0%
    assert res.get("score_pct") == 80.0
    assert res.get("findings_logged") >= 1

    # Verify finding exists and has linked CAPA
    iid = res["inspection_id"]
    detail = get_inspection_details(db, inspection_id=iid)
    assert len(detail.get("findings", [])) >= 1
    f = detail["findings"][0]
    assert f.get("capa_id") is not None


def test_get_inspection_stats_kpi(db):
    """3. Test AI Inspection Assistant Stats (مساعد التفتيش الذكي AI)."""
    stats = get_inspection_stats(db=db)
    assert not stats.get("error")
    assert "total_inspections" in stats
    assert "completed" in stats
    assert "scheduled" in stats
    assert "average_compliance_pct" in stats
    assert "open_findings" in stats
    assert isinstance(stats["summary"], str)


def test_log_fire_inspection_qr_simulation(db):
    """4. Test QR Scan Mobile Inspection (محاكاة مسح الكود) with equipment tags."""
    res = log_fire_inspection(
        db=db,
        equipment_tag="QR-FE-A-014",
        inspector="م. مصطفى",
        result="PASS",
        pressure_ok=True,
        hose_ok=True,
        safety_pin_ok=True,
        access_clear=True,
        notes="فحص دوري عبر محاكاة مسح كود QR - الحالة ممتازة"
    )
    assert res.get("success") is True
    assert res.get("inspection_id") is not None
    assert res.get("result") == "PASS"
    assert res.get("equipment_tag") is not None
    assert res.get("next_due_date") is not None


def test_findings_management_crud(db):
    """5. Test Findings Management (ملاحظات عدم المطابقة): create, list, close, and delete."""
    # Create finding
    res_create = create_inspection_finding(
        db=db,
        inspection_id=1,
        description="انسداد طفاية الحريق بالكراتين في ممر المستودع",
        category="الحماية من الحريق",
        severity="CRITICAL",
        due_days=3
    )
    assert res_create.get("success") is True
    fid = res_create.get("finding_id")
    assert fid is not None

    # Update status to CLOSED
    res_close = update_inspection_finding(
        db=db,
        finding_id=fid,
        status="CLOSED",
        notes="تم رفع الكراتين وفتح الممر أمام الطفاية بالكامل"
    )
    assert res_close.get("success") is True
    assert "CLOSED" in str(res_close.get("status"))

    # List findings
    res_list = list_inspection_findings(db=db, limit=10)
    assert res_list.get("count", 0) > 0

    # Delete finding
    res_del = delete_inspection_finding(db=db, finding_id=fid, reason="اختبار الأتمتة")
    assert res_del.get("success") is True


def test_generate_inspection_checklist_all_standards():
    """6. Test Form Builder (بانى نماذج التفتيش) across 6 standards."""
    standards = ["ISO_45001", "ISO_14001", "OSHA_1910", "NFPA", "BBS", "5S"]
    for std in standards:
        res = generate_inspection_checklist(standard=std, zone_name="خطوط العزل CCV")
        assert res.get("standard") == std
        assert len(res.get("items", [])) >= 4
        assert res.get("total_checkpoints", 0) >= 4


def test_nlp_inspection_intents_routing():
    """7. Test NLP keyword parser routing for inspection actions."""
    # Schedule walk
    q1 = "جدولة جولة تفتيش دورية في عنبر السحب للأسبوع القادم"
    p1 = parse_user_hse_prompt(q1)
    assert "SCHEDULE_INSPECTION" in p1.all_intents
    assert "schedule_safety_inspection" in p1.recommended_tools

    # Start live walk
    q2 = "بدء جولة تفتيش في خطوط العزل بنسبة التزام 98%"
    p2 = parse_user_hse_prompt(q2)
    assert "SUBMIT_INSPECTION_WALK" in p2.all_intents
    assert "submit_inspection_walk" in p2.recommended_tools

    # QR Scan simulation
    q3 = "محاكاة مسح الكود لطفاية الحريق QR-FE-A-014 وتأكيد الفحص"
    p3 = parse_user_hse_prompt(q3)
    assert "LOG_FIRE_INSPECTION" in p3.all_intents
    assert "log_fire_inspection" in p3.recommended_tools

    # Close finding
    q4 = "إغلاق ملاحظة عدم المطابقة رقم 5 بعد إزالة العوائق"
    p4 = parse_user_hse_prompt(q4)
    assert "UPDATE_INSPECTION_FINDING" in p4.all_intents
    assert "update_inspection_finding" in p4.recommended_tools
    entities4 = extract_entity_ids(q4)
    assert entities4.get("finding_id") == 5

    # Checklist generator
    q5 = "بانى نماذج التفتيش واقتراح قائمة فحص حسب معيار NFPA"
    p5 = parse_user_hse_prompt(q5)
    assert "GENERATE_INSPECTION_CHECKLIST" in p5.all_intents
    assert "generate_inspection_checklist" in p5.recommended_tools
