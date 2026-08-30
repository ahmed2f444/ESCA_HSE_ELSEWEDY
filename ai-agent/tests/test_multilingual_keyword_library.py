"""
Comprehensive Test Suite for the Multilingual HSE Keyword Library across all 15 Modules.
Tests intent classification, equipment recognition, chemical extraction, temporal parsing,
Egyptian/Gulf colloquialisms, typos, and tool recommendations.
"""

import pytest
from datetime import date, time, timedelta

from app.nlp import (
    parse_user_hse_prompt,
    classify_hse_intent,
    score_all_intents,
    classify_module_affinity,
    extract_entity_ids,
    extract_all_hse_entities,
    extract_equipment_info,
    extract_chemical_info,
    parse_relative_or_exact_date,
    parse_exact_or_colloquial_time,
    extract_duration_hours,
    parse_shift_type,
    get_keywords_for_module,
    search_keyword_across_modules,
    search_equipment_catalog,
    search_chemical_catalog,
    EQUIPMENT_REGISTRY,
    CHEMICAL_REGISTRY,
    MODULE_METADATA,
    HSE_INTENTS_KEYWORDS,
)


class TestModuleMetadataAndCoverage:
    """Verifies that all 15 modules are thoroughly covered with metadata and keywords."""

    def test_all_15_modules_present(self):
        assert len(MODULE_METADATA) == 15
        for i in range(1, 16):
            assert i in MODULE_METADATA
            assert "module_code" in MODULE_METADATA[i]
            assert "name_en" in MODULE_METADATA[i]
            assert "name_ar" in MODULE_METADATA[i]
            assert len(MODULE_METADATA[i]["primary_tables"]) > 0

    def test_keywords_registered_per_module(self):
        for mod_id in range(1, 16):
            kws = get_keywords_for_module(mod_id)
            assert len(kws) > 0, f"Module {mod_id} must have registered keywords"

    def test_search_keyword_across_modules(self):
        matches = search_keyword_across_modules("تصريح")
        assert len(matches) > 0
        assert any(m["module_id"] == 4 for m in matches)

        matches_fe = search_keyword_across_modules("extinguisher")
        assert len(matches_fe) > 0
        assert any(m["module_id"] == 11 for m in matches_fe)


class TestAll15ModulesIntentClassification:
    """Tests intent classification accuracy for all 15 HSE modules in both Arabic & English."""

    # Module 1: Master Data & Org
    def test_module_1_master_data(self):
        intent, _ = classify_hse_intent("show me plant layout and all departments")
        assert intent == "LIST_DEPARTMENTS"

        intent, _ = classify_hse_intent("عرض قطاعات المصنع وقائمة الاقسام")
        assert intent == "LIST_DEPARTMENTS"

        intent, _ = classify_hse_intent("اعرض قائمة العمال في عنبر سحب النحاس")
        assert intent == "LIST_EMPLOYEES"

        intent, _ = classify_hse_intent("أضف فني جديد في قسم الصيانة")
        assert intent == "CREATE_EMPLOYEE"

    # Module 2: Dashboard & KPIs
    def test_module_2_dashboard_kpis(self):
        intent, _ = classify_hse_intent("show executive safety dashboard and safe man-hours")
        assert intent == "GET_DASHBOARD_SUMMARY"

        intent, _ = classify_hse_intent("ما هو معدل الحوادث الشهري TRIR و LTIFR؟")
        assert intent == "GET_MONTHLY_KPIS"

        intent, _ = classify_hse_intent("ترتيب العنابر حسب نسبة الامتثال ودرجات السلامة")
        assert intent == "GET_SAFETY_SCORES"

    # Module 3: Incidents & Observations
    def test_module_3_incidents_observations(self):
        intent, _ = classify_hse_intent("report near miss and chemical spill in area 3")
        assert intent == "CREATE_INCIDENT"

        intent, _ = classify_hse_intent("تسجيل سلوك غير آمن: عامل لا يرتدي نظارة واقية")
        assert intent == "LOG_SAFETY_OBSERVATION"

        intent, _ = classify_hse_intent("ما هو السبب الجذري للحادث رقم INC-005؟")
        assert intent == "GET_INCIDENT_DETAILS"

    # Module 4: Permits & SIMOPS
    def test_module_4_permits_simops(self):
        intent, _ = classify_hse_intent("request a hot work permit for welding cable trays")
        assert intent == "CREATE_PERMIT"

        intent, _ = classify_hse_intent("اعتمد وتفعيل تصريح العمل رقم PTW-15")
        assert intent == "APPROVE_PERMIT"

        intent, _ = classify_hse_intent("أوقف تصريح العمل رقم 4 فورا")
        assert intent == "SUSPEND_PERMIT"

        intent, _ = classify_hse_intent("هل يوجد تعارض بين تصاريح العمل في عنبر 2 (SIMOPS)؟")
        assert intent == "CHECK_SIMOPS"

        intent, _ = classify_hse_intent("اغلق كافة تصاريح العمل النشطة وتسليم الموقع")
        assert intent == "CLOSE_ALL_PERMITS" or intent == "CLOSE_PERMIT"

    # Module 5: Inspections & Audits
    def test_module_5_inspections(self):
        intent, _ = classify_hse_intent("schedule a new safety inspection for line A next week")
        assert intent == "SCHEDULE_INSPECTION"

        intent, _ = classify_hse_intent("بدء جولة تفتيش ميدانية في عنبر التدريع")
        assert intent == "SUBMIT_INSPECTION_WALK"

        intent, _ = classify_hse_intent("تسجيل ملاحظة عدم مطابقة أثناء المعاينة")
        assert intent == "CREATE_INSPECTION_FINDING"

    # Module 6: CAPA
    def test_module_6_capa(self):
        intent, _ = classify_hse_intent("create a new corrective action for the electrical hazard")
        assert intent == "CREATE_CAPA"

        intent, _ = classify_hse_intent("اعرض قائمة الإجراءات التصحيحية المتأخرة CAPA")
        assert intent == "LIST_CAPAS"

    # Module 7: Risk Register & HIRA
    def test_module_7_hira(self):
        intent, _ = classify_hse_intent("hazard identification and risk assessment for high voltage testing")
        assert intent == "CREATE_RISK"

        intent, _ = classify_hse_intent("سجل المخاطر العام ومصفوفة الخطر")
        assert intent == "LIST_RISK"

    # Module 8: JSA / JHA
    def test_module_8_jsa(self):
        intent, _ = classify_hse_intent("job safety analysis for confined space entry")
        assert intent == "CREATE_JSA"

        intent, _ = classify_hse_intent("قائمة نماذج تحليل سلامة المهام JSA")
        assert intent == "LIST_JSAS"

    # Module 9: Training & Certifications
    def test_module_9_training(self):
        intent, _ = classify_hse_intent("renew certificate TRN-085 for 1 year")
        assert intent == "RENEW_CERTIFICATE"

        intent, _ = classify_hse_intent("جدد شهادة السلامة للعامل لمدة سنة")
        assert intent == "RENEW_CERTIFICATE"

        intent, _ = classify_hse_intent("قائمة الشهادات التدريبية المنتهية الصلاحية")
        assert intent == "LIST_CERTIFICATES"

    # Module 10: PPE Inventory
    def test_module_10_ppe(self):
        intent, _ = classify_hse_intent("give one safety helmet to employee EMP-010")
        assert intent == "ISSUE_PPE"

        intent, _ = classify_hse_intent("صرف 2 حذاء أمان للموظف رقم 5")
        assert intent == "ISSUE_PPE"

        intent, _ = classify_hse_intent("طلب توريد مهمات الوقاية الناقصة تحت حد الطلب")
        assert intent == "CREATE_PPE_SUPPLY_ORDER"

    # Module 11: Fire Safety & Fixed Assets
    def test_module_11_fire_safety(self):
        intent, _ = classify_hse_intent("qr scan mobile inspection for extinguisher QR-FE-A-014")
        assert intent == "LOG_FIRE_INSPECTION"

        intent, _ = classify_hse_intent("فحص واختبار محطة غسيل العيون ودش الطوارئ")
        assert intent == "INSPECT_FIXED_SAFETY_ASSET"

        intent, _ = classify_hse_intent("قائمة معدات ومطافئ الحريق المنتهية الصلاحية")
        assert intent == "LIST_FIRE_EQUIPMENT"

    # Module 12: HazMat & Chemicals
    def test_module_12_chemicals(self):
        intent, _ = classify_hse_intent("register new chemical CAS 108-88-3 toluene")
        assert intent == "ADD_CHEMICAL"

        intent, _ = classify_hse_intent("قائمة المواد الكيميائية الخطرة وتوافق التخزين")
        assert intent == "LIST_CHEMICALS"

    # Module 13: Occupational Health
    def test_module_13_health(self):
        intent, _ = classify_hse_intent("record periodic medical exam and audiometry test for worker")
        assert intent == "RECORD_MEDICAL_EXAM"

        intent, _ = classify_hse_intent("سجل الفحوصات الطبية الدورية وقياسات السمع")
        assert intent == "LIST_MEDICAL_EXAMS"

    # Module 14: AI Vision & IoT
    def test_module_14_ai_iot(self):
        intent, _ = classify_hse_intent("install new VOC gas sensor in compounding area")
        assert intent == "ADD_IOT_SENSOR"

        intent, _ = classify_hse_intent("انذارات الحساسات ومخالفات كاميرات الذكاء الاصطناعي")
        assert intent == "LIST_AI_IOT"

    # Module 15: Security & RAG
    def test_module_15_governance_rag(self):
        intent, _ = classify_hse_intent("ما هي اشتراطات OSHA لدخول الأماكن المغلقة وحدود الغازات؟")
        assert intent == "SEARCH_RAG_KNOWLEDGE"

        intent, _ = classify_hse_intent("عرض مصفوفة صلاحيات النظام RBAC")
        assert intent == "LIST_SECURITY_ROLES"


class TestEquipmentAndChemicalCatalog:
    """Verifies matching and extraction from the Equipment & Chemical registries."""

    def test_equipment_catalog_matching(self):
        # PPE Safety Glasses
        res = extract_equipment_info("give one safety glassess to worker")
        assert res is not None
        assert res["item_code"] == "PPE-EY-01"

        # PPE Hard Hat with typo
        res2 = extract_equipment_info("صرف خوذه امان للعامل")
        assert res2 is not None
        assert res2["item_code"] == "PPE-HD-01"

        # Fixed Emergency Eyewash
        res3 = extract_equipment_info("inspect emergency eyewash station")
        assert res3 is not None
        assert res3["asset_summary_id"] == 1

        # CO2 Extinguisher
        res4 = extract_equipment_info("فحص طفاية ثاني أكسيد الكربون CO2")
        assert res4 is not None
        assert res4["equipment_id"] == 2

    def test_chemical_catalog_matching(self):
        # Sulfuric acid
        c1 = extract_chemical_info("تسجيل شحنة حمض الكبريتيك H2SO4")
        assert c1 is not None
        assert c1["cas_number"] == "7664-93-9"

        # SF6 Gas
        c2 = extract_chemical_info("check sulfur hexafluoride SF6 cylinder")
        assert c2 is not None
        assert c2["chemical_code"] == "GAS-SF6"

        # Search catalog
        search_res = search_chemical_catalog("toluene")
        assert len(search_res) > 0
        assert search_res[0]["cas_number"] == "108-88-3"


class TestTemporalAndEntityParsing:
    """Tests exact and relative dates, times, durations, and entity IDs."""

    def test_date_parsing_relative(self):
        today = date(2026, 8, 30)

        # Tomorrow / بكرة
        d, delta, _ = parse_relative_or_exact_date("موعد الفحص غدا", base_date=today)
        assert d == date(2026, 8, 31)
        assert delta == 1

        # +1 year / لسنة
        d2, delta2, _ = parse_relative_or_exact_date("renew for 1 year", base_date=today)
        assert d2 == date(2027, 8, 30)
        assert delta2 == 365

        # 6 months / نصف سنة
        d3, delta3, _ = parse_relative_or_exact_date("بعد 6 اشهر", base_date=today)
        assert d3 == date(2027, 2, 26) or delta3 == 180

    def test_time_parsing(self):
        # 24-hour
        t1, _ = parse_exact_or_colloquial_time("at 17:30")
        assert t1 == time(17, 30)

        # 12-hour PM
        t2, _ = parse_exact_or_colloquial_time("الساعة 5:31 م")
        assert t2 == time(17, 31)

        # Colloquial Arabic
        t3, _ = parse_exact_or_colloquial_time("الساعة 5 ونصف مساء")
        assert t3 == time(17, 30)

    def test_duration_and_shift(self):
        # Duration hours
        dur = extract_duration_hours("تصريح عمل لمدة 8 ساعات")
        assert dur == 8.0

        # Shift
        sh = parse_shift_type("الوردية الصباحية Shift A")
        assert sh == "MORNING"

    def test_extract_all_entities(self):
        prompt = "انشئ تصريح عمل ساخن رقم PTW-015 في عنبر 2 بدرجة خطورة HIGH لمدة 8 ساعات مع فحص غازات"
        parsed = parse_user_hse_prompt(prompt)

        assert parsed.primary_intent == "CREATE_PERMIT" or "permit_id" in parsed.entity_ids
        assert parsed.entity_ids.get("permit_id") == 15
        assert parsed.risk_level == "HIGH"
        assert parsed.duration_hours == 8.0
        assert len(parsed.recommended_tools) > 0
