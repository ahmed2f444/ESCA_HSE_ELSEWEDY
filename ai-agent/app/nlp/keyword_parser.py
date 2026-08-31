"""
ESCA HSE AI Agent - Unified Multilingual Keyword Parser & NLP Subsystem

This module acts as the unified enterprise NLP pipeline and facade across all 15 ESCA HSE modules.
Combines orthographic normalization, date/time/shift parsing, multi-module intent routing,
entity recognition, equipment catalogs, chemical catalogs, and OpenAI tool recommendations.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict, Any

from .constants import (
    ARABIC_DIACRITICS,
    ARABIC_TATWEEL,
    RELATIVE_DAY_KEYWORDS,
    ARABIC_MONTHS,
    ENGLISH_MONTHS,
    WORD_TO_QUANTITY,
    SEVERITY_KEYWORDS,
    RISK_LEVEL_KEYWORDS,
    STATUS_TARGET_KEYWORDS,
)
from .normalization import (
    normalize_arabic,
    normalize_english,
    normalize_text,
    extract_word_tokens,
    contains_keyword_phrase,
)
from .date_time_parser import (
    parse_relative_or_exact_date,
    parse_exact_or_colloquial_time,
    extract_duration_hours,
    parse_shift_type,
)
from .equipment_library import (
    EQUIPMENT_REGISTRY,
    extract_equipment_info,
    search_equipment_catalog,
)
from .chemical_library import (
    CHEMICAL_REGISTRY,
    extract_chemical_info,
    search_chemical_catalog,
)
from .module_keywords import (
    MODULE_METADATA,
    HSE_INTENTS_KEYWORDS,
    INTENT_TO_MODULE_MAP,
    INTENT_TO_TOOL_MAP,
    get_keywords_for_module,
    search_keyword_across_modules,
)
from .entity_extractors import (
    extract_quantity,
    extract_severity_level,
    extract_risk_level,
    extract_status_target,
    extract_zone_info,
    extract_entity_ids,
    extract_all_hse_entities,
)
from .intent_classifier import (
    score_all_intents,
    classify_hse_intent,
    classify_module_affinity,
)


# ==============================================================================
# UNIFIED PARSED HSE PROMPT DATACLASS
# ==============================================================================

@dataclass
class ParsedHsePrompt:
    """Structured container for deep NLP parsing results of an HSE query."""
    raw_prompt: str
    normalized_prompt: str
    primary_intent: Optional[str] = None
    all_intents: List[str] = field(default_factory=list)
    recommended_tools: List[str] = field(default_factory=list)
    entity_ids: Dict[str, Any] = field(default_factory=dict)
    target_date: Optional[date] = None
    target_time: Optional[time] = None
    target_datetime: Optional[datetime] = None
    days_delta: Optional[int] = None
    date_match_type: Optional[str] = None
    time_match_type: Optional[str] = None
    duration_hours: Optional[float] = None
    shift_type: Optional[str] = None
    is_crud_mutation: bool = False
    status_target: Optional[str] = None
    severity: Optional[str] = None
    risk_level: Optional[str] = None
    module_affinities: List[Dict[str, Any]] = field(default_factory=list)


# ==============================================================================
# COMPREHENSIVE PROMPT PARSING ENGINE
# ==============================================================================

def parse_user_hse_prompt(text: str, base_date: Optional[date] = None) -> ParsedHsePrompt:
    """
    Main parsing entrypoint: Analyzes user prompt in Arabic or English across all 15 HSE modules.
    Extracts intents, entities, temporal parameters, equipment, chemicals, mutations, and recommended tools.
    """
    today = base_date or date.today()
    norm = normalize_text(text)

    # 1. Intent Classification & Module Affinity
    primary_intent, all_intents = classify_hse_intent(text)
    module_affinities = classify_module_affinity(text)

    # 2. Entity IDs, Equipment, Chemicals, Zones, Quantities
    entity_ids = extract_entity_ids(text)

    # 3. Date & Time Parsing
    target_date, days_delta, date_type = parse_relative_or_exact_date(text, base_date=today)
    target_time, time_type = parse_exact_or_colloquial_time(text)
    duration_hours = extract_duration_hours(text)
    shift_type = parse_shift_type(text)

    target_datetime = None
    resolved_d = target_date or today
    resolved_t = target_time or time(23, 59)
    if target_date or target_time:
        target_datetime = datetime.combine(resolved_d, resolved_t)

    # 4. Status, Severity & Risk Targets
    status_target = extract_status_target(text)
    severity = extract_severity_level(text)
    risk_level = extract_risk_level(text)

    # 5. Mutation check & Entity-specific intent override
    mutation_keywords = [
        "renew", "تجديد", "جدد", "تمديد", "تعديل", "تحديث", "تغيير", "update", "modify", "change", "edit", "move", "set",
        "صرف", "انشئ", "أنشئ", "سجل", "أضف", "اضف", "create", "add", "issue", "approve", "اعتمد", "احذف", "delete", "cancel",
        "الغاء", "إلغاء", "امسح", "شطب", "فعل", "activate", "sign", "close", "اغلق", "أغلق", "إغلاق", "انهاء", "إنهاء"
    ]
    is_crud = any(k in norm for k in mutation_keywords)

    # Disambiguation Rules for High-Impact Actions
    if any(w in norm for w in [
        "export excel", "export to excel", "export incident", "تصدير excel", "تصدير اكسل", "تصدير الإكسل",
        "تصدير الحوادث", "سجل الحوادث excel", "شيت اكسل", "تحميل اكسل", "تصدير السجل"
    ]):
        primary_intent = "EXPORT_INCIDENTS_EXCEL"
        if "EXPORT_INCIDENTS_EXCEL" not in all_intents:
            all_intents.insert(0, "EXPORT_INCIDENTS_EXCEL")

    elif any(w in norm for w in [
        "توليد نموذج", "نموذج مكتب العمل", "نموذج التأمينات", "استمارة 1", "مطالبة التأمين", "مطالبة شركة التأمين",
        "إخطار جهاز شؤون البيئة", "إخطار البيئة", "قوالب الإبلاغ الخارجي", "قوالب الابلاغ الخارجي",
        "labor office form", "social insurance form", "insurance claim form", "environmental agency notification"
    ]):
        primary_intent = "GENERATE_REPORT_TEMPLATE"
        if "GENERATE_REPORT_TEMPLATE" not in all_intents:
            all_intents.insert(0, "GENERATE_REPORT_TEMPLATE")

    elif any(w in norm for w in [
        "تحليل الأسباب الجذرية — ytd", "تحليل الأسباب الجذرية ytd", "الأسباب الجذرية الأكثر تكراراً",
        "نسب أسباب الحوادث", "ملخص الأسباب الجذرية", "root causes ytd", "root cause breakdown"
    ]):
        primary_intent = "GET_ROOT_CAUSES"
        if "GET_ROOT_CAUSES" not in all_intents:
            all_intents.insert(0, "GET_ROOT_CAUSES")

    elif any(w in norm for w in [
        "تحليل السبب الجذري", "سجل تحليل السبب الجذري", "تحليل rca", "إضافة تحليل السبب الجذري",
        "توثيق rca", "السبب الجذري للحادث", "5 whys", "fishbone", "عظم السمكة", "إيشيكاوا", "root cause analysis"
    ]):
        primary_intent = "MANAGE_RCA"
        if "MANAGE_RCA" not in all_intents:
            all_intents.insert(0, "MANAGE_RCA")

    elif any(w in norm for w in [
        "تحديث لوحة القيادة", "تحديث لوحه القياده", "تحديث الداشبورد", "تحديث البيانات", "إعادة تحميل لوحة القيادة",
        "تحديث مؤشرات السلامة", "refresh dashboard", "refresh stats", "reload dashboard data"
    ]) and len(norm.split()) <= 6:
        primary_intent = "REFRESH_DASHBOARD"
        if "REFRESH_DASHBOARD" not in all_intents:
            all_intents.insert(0, "REFRESH_DASHBOARD")

    elif any(w in norm for w in [
        "medical exam", "medical examination", "health exam", "health examination",
        "audiometry", "spirometry", "hearing exam", "hearing check", "hearing test",
        "lung function", "fitness for duty", "fitness exam", "create medical",
        "record medical", "schedule medical", "record exam", "schedule exam",
        "فحص طبي", "كشف طبي", "فحص سمع", "كشف سمع", "فحص السمع", "كشف اللياقة",
        "جدولة كشف", "تسجيل فحص", "إنشاء سجل طبي", "سجل طبي",
    ]) and any(w in norm for w in [
        "create", "add", "record", "schedule", "register", "make", "new", "log",
        "أنشئ", "سجل", "أضف", "اضف", "جدول", "كشف", "فحص", "أنشئ",
    ]):
        primary_intent = "RECORD_MEDICAL_EXAM"
        if "RECORD_MEDICAL_EXAM" not in all_intents:
            all_intents.insert(0, "RECORD_MEDICAL_EXAM")

    # ── HazMat & Chemicals Disambiguation Rules ───────────────────────────
    chem_match = extract_chemical_info(text)
    has_chem_action = any(w in norm for w in [
        "add", "new", "create", "register", "insert", "store",
        "اضف", "اضافه", "إضافة", "اضافة", "سجل", "تسجيل", "حط", "حطلي", "ادخل", "ادخال", "انشاء", "انشئ"
    ])
    has_hazmat_target = any(w in norm for w in [
        "hazardous material", "hazardous materials", "hazmat", "chemical", "chemicals",
        "ماده جديده", "ماده خطره", "المواد الخطره", "المواد الخطرة", "المواد الكيميائيه", "المواد الكيميائية",
        "الكيماويات", "كيماويات", "كيميائيه جديده", "مخزون المواد الخطره", "سجل المواد الخطره", "سجل الكيماويات",
        "ماده", "مادة"
    ]) or (chem_match is not None)

    if has_chem_action and has_hazmat_target:
        primary_intent = "ADD_CHEMICAL"
        if "ADD_CHEMICAL" not in all_intents:
            all_intents.insert(0, "ADD_CHEMICAL")

    elif any(w in norm for w in [
        "تعليمات الطوارئ", "مكافحة الانسكاب", "مكافحه الانسكاب", "طوارئ المواد", "طوارئ مادة", "طوارئ ماده",
        "اسعافات اولية لمادة", "اسعافات اوليه لماده", "مهمات الوقاية لمادة", "دليل طوارئ المواد", "دليل طوارئ",
        "emergency guide", "chemical emergency", "spill response"
    ]):
        primary_intent = "EMERGENCY_GUIDE"
        if "EMERGENCY_GUIDE" not in all_intents:
            all_intents.insert(0, "EMERGENCY_GUIDE")

    elif any(w in norm for w in [
        "ارشيف صحائف السلامة", "ارشيف صحائف السلامه", "صحائف السلامة", "صحائف السلامه", "صحائف بيانات السلامة",
        "سجل sds", "ارشيف sds", "أرشيف sds", "sds archive", "list sds", "sds records", "sds library"
    ]):
        primary_intent = "SDS_ARCHIVE"
        if "SDS_ARCHIVE" not in all_intents:
            all_intents.insert(0, "SDS_ARCHIVE")

    elif any(w in norm for w in [
        "تفاصيل مادة", "تفاصيل ماده", "بيانات مادة", "بيانات ماده", "معلومات مادة", "معلومات ماده", "كارت مادة",
        "كارت ماده", "بطاقة مادة", "بطاقه ماده", "كارت السلامة", "كارت السلامه",
        "chemical details", "chemical profile", "chemical card", "hazmat profile", "substance details"
    ]) or (chem_match is not None and any(w in norm for w in ["تفاصيل", "بيانات", "معلومات", "كارت", "بطاقه", "بطاقة", "اعرض", "عرض", "show", "get", "view", "details", "profile"])):
        primary_intent = "GET_CHEMICAL_DETAILS"
        if "GET_CHEMICAL_DETAILS" not in all_intents:
            all_intents.insert(0, "GET_CHEMICAL_DETAILS")

    elif any(w in norm for w in ["عدل كمية", "عدل كميه", "تعديل كمية", "تعديل كميه", "تعديل مادة", "تعديل ماده", "تحديث مخزون", "تعديل بيانات مادة", "تحديث كمية", "تحديث كميه", "update chemical", "update stock", "change quantity"]) and (has_hazmat_target or chem_match is not None or any(w in norm for w in ["مادة", "ماده", "chemical", "كجم", "لتر", "kg", "liters"])):
        primary_intent = "UPDATE_CHEMICAL"
        if "UPDATE_CHEMICAL" not in all_intents:
            all_intents.insert(0, "UPDATE_CHEMICAL")

    elif any(w in norm for w in ["احذف مادة", "احذف ماده", "امسح مادة", "امسح ماده", "حذف مادة", "حذف ماده", "delete chemical", "remove chemical", "purge chemical", "delete from hazmat", "احذف من المواد الخطرة", "احذف من المواد الخطره"]):
        primary_intent = "DELETE_CHEMICAL"
        if "DELETE_CHEMICAL" not in all_intents:
            all_intents.insert(0, "DELETE_CHEMICAL")

    elif any(w in norm for w in ["فحص التوافق", "توافق المواد", "امان التخزين", "أمان التخزين", "تخزين الكيماويات", "توافق التخزين", "chemical compatibility", "storage safety", "hazmat compatibility"]):
        primary_intent = "CHECK_CHEMICAL_STORAGE"
        if "CHECK_CHEMICAL_STORAGE" not in all_intents:
            all_intents.insert(0, "CHECK_CHEMICAL_STORAGE")

    elif any(w in norm for w in [
        "المواد الخطرة", "المواد الخطره", "المواد الخطرة والكيماويات", "المواد الخطره والكيماويات", "المواد الكيميائية", "المواد الكيميائيه",
        "المواد القابلة للاشتعال", "المواد القابله للاشتعال", "المواد المؤكسدة", "المواد المؤكسده", "المواد الأكالة", "المواد الاكاله", "المواد السامة", "المواد السامه", "سجل المواد الخطرة", "سجل المواد الخطره",
        "المواد المسجلة", "المواد المسجله", "قائمة المواد", "قائمه المواد", "قائمة المواد الخطرة", "قائمه المواد الخطره", "مخزون الكيماويات", "سجل الكيماويات",
        "list chemicals", "flammable chemicals", "hazardous materials", "hazmat inventory", "hazmat catalog", "chemical inventory"
    ]) and not has_chem_action:
        primary_intent = "LIST_CHEMICALS"
        if "LIST_CHEMICALS" not in all_intents:
            all_intents.insert(0, "LIST_CHEMICALS")

    elif any(w in norm for w in [
        "close all", "اغلق كافة", "إغلاق كافة", "اغلق جميع", "إغلاق جميع", "اغلق كل", "إغلاق كل",
        "إنهاء كافة", "انهاء كافة", "إنهاء جميع", "انهاء جميع"
    ]):
        primary_intent = "CLOSE_ALL_PERMITS"
        if "CLOSE_ALL_PERMITS" not in all_intents:
            all_intents.insert(0, "CLOSE_ALL_PERMITS")

    elif "permit_id" in entity_ids:
        if any(w in norm for w in ["delete", "remove", "purge", "cancel", "احذف", "امسح", "شطب", "الغاء", "إلغاء"]):
            primary_intent = "DELETE_PERMIT"
            if "DELETE_PERMIT" not in all_intents:
                all_intents.insert(0, "DELETE_PERMIT")
        elif any(w in norm for w in ["approve", "activate", "sign", "اعتماد", "اعتمد", "تفعيل", "فعل"]):
            primary_intent = "APPROVE_PERMIT"
            if "APPROVE_PERMIT" not in all_intents:
                all_intents.insert(0, "APPROVE_PERMIT")
        elif any(w in norm for w in ["suspend", "freeze", "halt", "stop", "اوقف", "أوقف", "علق", "تعليق", "إيقاف", "ايقاف"]):
            primary_intent = "SUSPEND_PERMIT"
            if "SUSPEND_PERMIT" not in all_intents:
                all_intents.insert(0, "SUSPEND_PERMIT")
        elif any(w in norm for w in ["close", "complete", "finish", "اغلق", "أغلق", "إغلاق", "انهاء", "إنهاء", "تسليم"]):
            primary_intent = "CLOSE_PERMIT"
            if "CLOSE_PERMIT" not in all_intents:
                all_intents.insert(0, "CLOSE_PERMIT")
        elif any(w in norm for w in [
            "change", "update", "modify", "extend", "edit", "move", "set", "location", "zone", "description",
            "contractor", "executor", "hours", "duration", "risk", "تعديل", "تغيير", "تحديث", "تمديد", "نقل",
            "موقع", "مكان", "عنبر", "وصف", "مقاول", "منفذ", "ساعات", "مدة", "خطورة"
        ]):
            if not primary_intent or primary_intent not in ("APPROVE_PERMIT", "SUSPEND_PERMIT", "CLOSE_PERMIT"):
                primary_intent = "UPDATE_PERMIT"
                if "UPDATE_PERMIT" not in all_intents:
                    all_intents.insert(0, "UPDATE_PERMIT")
        elif not primary_intent:
            primary_intent = "GET_PERMIT_DETAILS"
            if "GET_PERMIT_DETAILS" not in all_intents:
                all_intents.append("GET_PERMIT_DETAILS")

    elif "certificate_id" in entity_ids:
        if any(w in norm for w in ["renew", "extend", "refresh", "تجديد", "جدد", "تمديد", "مد صلاحية"]):
            primary_intent = "RENEW_CERTIFICATE"
            if "RENEW_CERTIFICATE" not in all_intents:
                all_intents.insert(0, "RENEW_CERTIFICATE")

    # 6. Tool Recommendation Routing
    tools = []
    if primary_intent and primary_intent in INTENT_TO_TOOL_MAP:
        tools.extend(INTENT_TO_TOOL_MAP[primary_intent])
    for intent in all_intents[1:]:
        if intent in INTENT_TO_TOOL_MAP:
            for t in INTENT_TO_TOOL_MAP[intent]:
                if t not in tools:
                    tools.append(t)
    
    # Cap at max 6 tools to keep token footprint well balanced and comprehensive
    return ParsedHsePrompt(
        raw_prompt=text,
        normalized_prompt=norm,
        primary_intent=primary_intent,
        all_intents=all_intents,
        recommended_tools=tools[:6],
        entity_ids=entity_ids,
        target_date=target_date,
        target_time=target_time,
        target_datetime=target_datetime,
        days_delta=days_delta,
        date_match_type=date_type,
        time_match_type=time_type,
        duration_hours=duration_hours,
        shift_type=shift_type,
        is_crud_mutation=is_crud,
        status_target=status_target,
        severity=severity,
        risk_level=risk_level,
        module_affinities=module_affinities,
    )


def get_recommended_tools_for_prompt(text: str, all_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper to filter available OpenAI tool definitions based on parsed intent."""
    parsed = parse_user_hse_prompt(text)
    tool_map = {t["function"]["name"]: t for t in all_tools if "function" in t and "name" in t["function"]}
    selected = []

    for t_name in parsed.recommended_tools:
        if t_name in tool_map and tool_map[t_name] not in selected:
            selected.append(tool_map[t_name])

    if "search_hse_knowledge" in tool_map and tool_map["search_hse_knowledge"] not in selected:
        selected.append(tool_map["search_hse_knowledge"])

    if not selected:
        fallback_names = [
            "get_dashboard_summary", "list_incidents", "list_permits", "list_inspections",
            "search_hse_knowledge", "run_read_only_query"
        ]
        for fn in fallback_names:
            if fn in tool_map and tool_map[fn] not in selected:
                selected.append(tool_map[fn])

    return selected[:6]


# Export all public components
__all__ = [
    "ParsedHsePrompt",
    "parse_user_hse_prompt",
    "parse_relative_or_exact_date",
    "parse_exact_or_colloquial_time",
    "extract_duration_hours",
    "parse_shift_type",
    "extract_entity_ids",
    "extract_all_hse_entities",
    "extract_quantity",
    "extract_severity_level",
    "extract_risk_level",
    "extract_status_target",
    "extract_zone_info",
    "extract_equipment_info",
    "extract_chemical_info",
    "classify_hse_intent",
    "score_all_intents",
    "classify_module_affinity",
    "normalize_text",
    "normalize_arabic",
    "normalize_english",
    "extract_word_tokens",
    "get_recommended_tools_for_prompt",
    "get_keywords_for_module",
    "search_keyword_across_modules",
    "search_equipment_catalog",
    "search_chemical_catalog",
    "EQUIPMENT_REGISTRY",
    "CHEMICAL_REGISTRY",
    "MODULE_METADATA",
    "HSE_INTENTS_KEYWORDS",
    "INTENT_TO_MODULE_MAP",
    "INTENT_TO_TOOL_MAP",
    "RELATIVE_DAY_KEYWORDS",
    "SEVERITY_KEYWORDS",
    "RISK_LEVEL_KEYWORDS",
    "STATUS_TARGET_KEYWORDS",
]
