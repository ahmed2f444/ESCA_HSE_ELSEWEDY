import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.tools.rbac import check_tool_access
from app.nlp.chemical_library import extract_chemical_info, search_chemical_catalog
from app.nlp.keyword_parser import parse_user_hse_prompt, get_recommended_tools_for_prompt
from app.tools.handlers import (
    add_chemical,
    list_chemicals,
    get_chemical_details,
    get_chemical_compatibility,
    check_chemical_storage_safety,
    get_msds_sheet,
    get_chemical_emergency_guide,
    list_sds_records
)
from app.agent import run_agent_loop, _format_fallback_table
from app.schemas import AskResponse


# ── 1. RBAC Tests for Production Supervisor & HSE Roles ───────────────────────
def test_production_supervisor_hazmat_rbac_permissions():
    role = "ROLE_PRODUCTION_SUPERVISOR"
    hazmat_tools = [
        "add_chemical",
        "list_chemicals",
        "get_chemical_details",
        "get_chemical_compatibility",
        "check_chemical_storage_safety",
        "update_chemical",
        "update_chemical_stock",
        "delete_chemical",
        "get_msds_sheet",
        "get_chemical_emergency_guide",
        "list_sds_records"
    ]
    for t_name in hazmat_tools:
        is_auth, msg = check_tool_access(role, t_name)
        assert is_auth is True, f"Role {role} should have permission for {t_name}, but got: {msg}"


# ── 2. NLP Typo Resilience & Chemical Library Tests ──────────────────────────
def test_chemical_typo_resolution():
    # User prompt typos: "calcuim cianade"
    match = extract_chemical_info("add calcuim cianade to the hazardous materials")
    assert match is not None
    assert "Calcium Cyanide" in match["trade_name"]
    assert match["cas_number"] == "592-01-8"
    assert "FATAL_ORAL" in match["ghs_classes"] or "GHS06_TOXIC" in str(match["ghs_classes"])

    # Arabic prompt: "اضافة سيانيد الكالسيوم الى المواد الخطرة"
    match_ar = extract_chemical_info("اضافة سيانيد الكالسيوم الى المواد الخطرة")
    assert match_ar is not None
    assert match_ar["cas_number"] == "592-01-8"

    # Sodium Pentoxide
    match_pentoxide = extract_chemical_info("sodium pentoxide")
    assert match_pentoxide is not None
    assert match_pentoxide["cas_number"] == "12034-11-6"

    # Expanded Chemical Catalog Checks across all 9 categories
    test_chems = [
        ("حمض الهيدروفلوريك", "7664-39-3"),
        ("حمض الخليك الثلجي", "64-19-7"),
        ("هيدروكسيد البوتاسيوم", "1310-58-3"),
        ("ميثانول نقي", "67-56-1"),
        ("مذيب thf", "109-99-9"),
        ("ميثيلين كلورايد dcm", "75-09-2"),
        ("وايت سبيريت", "64742-82-1"),
        ("حبيبات lszh المقاومة للحريق", "9002-88-4"),
        ("دايكوميل بيروكسيد dcp", "80-43-3"),
        ("قضبان نحاس الكتروليتي", "7440-50-8"),
        ("غاز سداسي فلوريد الكبريت sf6", "2551-62-4"),
        ("كبريتيد الهيدروجين h2s", "7783-06-4"),
        ("هيبوكلوريت الصوديوم", "7681-52-9"),
        ("زيت عزل المحولات الكهربائية", "64742-53-6"),
        ("مخثر كلوريد الحديديك fecl3", "7705-08-0"),
        ("بولي ألومنيوم كلورايد pac", "1327-41-9"),
    ]
    for prompt_text, expected_cas in test_chems:
        res = extract_chemical_info(prompt_text)
        assert res is not None, f"Failed to match chemical from '{prompt_text}'"
        assert res["cas_number"] == expected_cas, f"Expected CAS {expected_cas} for '{prompt_text}', got {res['cas_number']}"


# ── 3. Prompt Intent Classification & Tool Recommendations ───────────────────
def test_hazmat_intent_classification():
    # Exact prompt from user screenshot
    p1 = parse_user_hse_prompt("add calcuim cianade to the hazardous materials")
    assert p1.primary_intent == "ADD_CHEMICAL"
    assert "add_chemical" in p1.recommended_tools

    # Arabic variant
    p2 = parse_user_hse_prompt("اضافة سيانيد الكالسيوم الى المواد الخطرة")
    assert p2.primary_intent == "ADD_CHEMICAL"
    assert "add_chemical" in p2.recommended_tools

    # Storage safety check
    p3 = parse_user_hse_prompt("فحص سلامة تخزين الكيماويات والتوافق")
    assert p3.primary_intent == "CHECK_CHEMICAL_STORAGE"
    assert "check_chemical_storage_safety" in p3.recommended_tools

    # Emergency Guide
    p4 = parse_user_hse_prompt("دليل طوارئ المواد الخطرة ومكافحة الانسكاب لسيانيد الكالسيوم")
    assert p4.primary_intent == "EMERGENCY_GUIDE"
    assert "get_chemical_emergency_guide" in p4.recommended_tools


# ── 4. Chemical Handler Execution & SDS Synchronization ──────────────────────
def test_add_chemical_handler_with_catalog_resolution():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = None  # Not existing
    mock_db.execute.return_value.scalar.return_value = 42      # New chemical_id

    result = add_chemical(
        db=mock_db,
        trade_name="calcuim cianade",
        quantity=50.0,
        zone_id=9
    )

    assert result.get("success") is True
    assert result.get("chemical_id") == 42
    assert result.get("cas_number") == "592-01-8"
    assert "Calcium Cyanide" in result.get("trade_name") or "سيانيد الكالسيوم" in result.get("chemical_name")
    assert result.get("unit") == "KG"
    assert mock_db.commit.called


def test_check_chemical_storage_safety_cyanide_acid_segregation():
    mock_db = MagicMock()
    # Mock finding Cyanide and Corrosive Acid in the same zone
    mock_db.execute.return_value.mappings.return_value = [
        {"chemical_id": 1, "trade_name": "Calcium Cyanide", "chemical_name": "Calcium Cyanide", "ghs_classes": "Fatal Oral", "storage_class": "Class 6 Toxic", "quantity": 50, "unit": "KG"},
        {"chemical_id": 2, "trade_name": "Sulfuric Acid", "chemical_name": "Sulfuric Acid", "ghs_classes": "Corrosive", "storage_class": "Class 8 Corrosive", "quantity": 100, "unit": "Liters"}
    ]

    result = check_chemical_storage_safety(db=mock_db, zone_id=9)
    assert result.get("success") is True
    assert result.get("is_safe_and_compliant") is False
    assert len(result.get("hazard_warnings")) > 0
    assert any("سيانيد الهيدروجين" in w or "HCN" in w for w in result.get("hazard_warnings"))


# ── 5. End-to-End Agent Loop Test for User Prompt ────────────────────────────
def test_agent_loop_add_calcium_cyanide_user_prompt():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = None
    mock_db.execute.return_value.scalar.return_value = 101

    # Simulate Turn 0 model refusing mutation, triggering interceptor safeguard, then Turn 1 synthesizing output
    msg_turn0 = MagicMock()
    msg_turn0.tool_calls = None
    msg_turn0.content = "عذراً، لا تتوفر حالياً وظيفة في النظام لإضافة مواد خطرة إلى قاعدة البيانات. يمكنني بدلاً من ذلك البحث عن معلومات السلامة."
    res_turn0 = MagicMock(choices=[MagicMock(message=msg_turn0)])

    msg_turn1 = MagicMock()
    msg_turn1.tool_calls = None
    msg_turn1.content = "تم تسجيل مادة سيانيد الكالسيوم (Calcium Cyanide) بنجاح في سجل المواد الخطرة (الرقم: CHM-101، الكمية: 100 كجم، CAS: 592-01-8) في العنبر 9."
    res_turn1 = MagicMock(choices=[MagicMock(message=msg_turn1)])

    with patch("app.agent.chat_completion", side_effect=[(res_turn0, "Groq (qwen/qwen3.6-27b)"), (res_turn1, "Groq (qwen/qwen3.6-27b)")]):
        resp = run_agent_loop(
            question="add calcuim cianade to the hazardous materials",
            db=mock_db,
            session_id="hazmat-test-session",
            user_role="Production Supervisor",
            model_mode="groq"
        )

        assert isinstance(resp, AskResponse)
        assert len(resp.tool_calls) > 0
        trace = resp.tool_calls[0]
        assert trace.tool_name == "add_chemical"
        assert trace.result.get("success") is True
        assert trace.result.get("cas_number") == "592-01-8"
        assert "سيانيد الكالسيوم" in resp.answer or "Calcium Cyanide" in resp.answer or "المواد الخطرة" in resp.answer


# ── 6. FastAPI Router Endpoints Test ─────────────────────────────────────────
def test_hazmat_fastapi_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Test GET /api/v1/hazmat/stats
    res_stats = client.get("/api/v1/hazmat/stats")
    assert res_stats.status_code == 200
    data_stats = res_stats.json()
    assert "totalChemicals" in data_stats
    assert "complianceRate" in data_stats

    # Test GET /api/v1/hazmat/compatibility
    res_compat = client.get("/api/v1/hazmat/compatibility?chemicalA=Cyanides&chemicalB=Acids")
    assert res_compat.status_code == 200
    data_compat = res_compat.json()
    assert "compatibility_matrix" in data_compat

    # Test GET /api/v1/hazmat/storage-safety
    res_storage = client.get("/api/v1/hazmat/storage-safety?zoneId=9")
    assert res_storage.status_code == 200


# ── 7. Arabic Ethyl Alcohol Prompt Resolution Test ──────────────────────────
def test_agent_loop_add_ethyl_alcohol_arabic_user_prompt():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = None
    mock_db.execute.return_value.scalar.return_value = 102

    # Test exact prompt from user screenshot: "حط ماده ايثايل الكحول في المواد الخطره"
    match = extract_chemical_info("حط ماده ايثايل الكحول في المواد الخطره")
    assert match is not None
    assert match["cas_number"] == "64-17-5"
    assert "Ethanol" in match["trade_name"] or "Ethyl Alcohol" in match["chemical_name"]

    p = parse_user_hse_prompt("حط ماده ايثايل الكحول في المواد الخطره")
    assert p.primary_intent == "ADD_CHEMICAL"
    assert "add_chemical" in p.recommended_tools

    msg_turn0 = MagicMock(tool_calls=None, content="عذراً، لا تتوفر حالياً وظيفة.")
    msg_turn1 = MagicMock(tool_calls=None, content="تم تسجيل مادة كحول الإيثيل (Ethanol) بنجاح في سجل المواد الخطرة.")

    with patch("app.agent.chat_completion", side_effect=[(MagicMock(choices=[MagicMock(message=msg_turn0)]), "Groq"), (MagicMock(choices=[MagicMock(message=msg_turn1)]), "Groq")]):
        resp = run_agent_loop(
            question="حط ماده ايثايل الكحول في المواد الخطره",
            db=mock_db,
            session_id="hazmat-ethanol-session",
            user_role="Production Supervisor",
            model_mode="groq"
        )

        assert isinstance(resp, AskResponse)
        assert len(resp.tool_calls) > 0
        trace = resp.tool_calls[0]
        assert trace.tool_name == "add_chemical"
        assert trace.result.get("success") is True
        assert trace.result.get("cas_number") == "64-17-5"
        assert "Ethanol" in str(trace.result) or "كحول" in str(trace.result) or "ايثايل" in str(trace.result)
