"""
ESCA HSE AI Agent - Comprehensive Multilingual Keyword Parser & NLP Library

This module provides a rich, enterprise-grade keyword extraction, intent classification,
relative/exact date-time parsing, and entity recognition library for the Elsewedy Cables (ESCA)
Health, Safety & Environment platform across all 15 modules.

Supports:
- Arabic (Modern Standard, Egyptian Dialect, Gulf/Levantine common terms)
- English (Formal, Colloquial, Abbreviations, Short Codes)
- Relative & Exact Dates (+1 year, tomorrow, next week, YYYY-MM-DD, DD/MM/YYYY, etc.)
- Exact & Colloquial Times (5:31 PM, 17:31, الساعة 5 ونصف, 5:31 م, etc.)
- Domain ID Extraction (TRN-085, INC-001, PTW-002, CAPA-003, JSA-004, EXT-005, etc.)
- Multi-Module HSE Action & CRUD Intent Routing
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Optional


# ==============================================================================
# 1. TEXT NORMALIZATION & DIACRITICS STRIPPING
# ==============================================================================

ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
ARABIC_TATWEEL = re.compile(r"\u0640")

def normalize_arabic(text: str) -> str:
    """Removes diacritics, tatweel, and normalizes Arabic letter variations."""
    if not text:
        return ""
    text = ARABIC_DIACRITICS.sub("", text)
    text = ARABIC_TATWEEL.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة\b", "ه", text)
    text = re.sub(r"[ىي]\b", "ي", text)
    return text

def normalize_text(text: str) -> str:
    """Full normalization for Arabic and English text matching."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = normalize_arabic(text)
    return text.lower().strip()

def extract_word_tokens(text: str) -> list[str]:
    """Extracts normalized words and strips common Arabic attached prepositions (لـ, بـ, كـ, فـ, وـ)."""
    norm = normalize_text(text)
    raw_tokens = re.findall(r"[\w-]+", norm)
    tokens = set(raw_tokens)
    for t in raw_tokens:
        if len(t) > 3 and t[0] in ["ل", "ب", "ف", "ك", "و"]:
            tokens.add(t[1:])
        if len(t) > 4 and t.startswith("ال"):
            tokens.add(t[2:])
            if len(t) > 5 and t[2] in ["ل", "ب", "ف", "ك", "و"]:
                tokens.add(t[3:])
    return list(tokens)


# ==============================================================================
# 2. RELATIVE DAY & DATE DICTIONARY
# ==============================================================================

RELATIVE_DAY_KEYWORDS: dict[str, int] = {
    # TODAY (0 days)
    "today": 0, "now": 0, "current": 0, "present": 0,
    "اليوم": 0, "النهارده": 0, "النهاردة": 0, "دلوقتي": 0, "الان": 0, "الآن": 0,
    "اليوم الحالي": 0, "في الوقت الحالي": 0, "هذا اليوم": 0, "حاليا": 0, "حالياً": 0,

    # TOMORROW (1 day)
    "tomorrow": 1, "tommorow": 1, "tmrw": 1, "2moro": 1, "next day": 1, "following day": 1,
    "غدا": 1, "غداً": 1, "بكرة": 1, "بكره": 1, "تاني يوم": 1, "الغد": 1, "يوم غد": 1,

    # DAY AFTER TOMORROW (2 days)
    "day after tomorrow": 2, "after tomorrow": 2, "in 2 days": 2, "+2 days": 2, "2 days": 2,
    "بعد غد": 2, "بعد غدا": 2, "بعد بكره": 2, "بعد بكرة": 2, "بعد يومين": 2, "يومين": 2,

    # 1 WEEK (7 days)
    "1 week": 7, "one week": 7, "next week": 7, "in a week": 7, "+1 week": 7, "+1w": 7,
    "اسبوع": 7, "أسبوع": 7, "بعد اسبوع": 7, "بعد أسبوع": 7, "اسبوع قادم": 7, "الأسبوع القادم": 7,

    # 1 MONTH (30 days)
    "1 month": 30, "one month": 30, "in a month": 30, "next month": 30, "+1 month": 30, "+1m": 30,
    "شهر": 30, "شهر واحد": 30, "بعد شهر": 30, "الشهر القادم": 30, "لمدة شهر": 30, "لشهر": 30,

    # 6 MONTHS (180 days)
    "6 months": 180, "six months": 180, "half year": 180, "+6 months": 180, "+6m": 180,
    "6 اشهر": 180, "6 أشهر": 180, "ستة اشهر": 180, "ستة أشهر": 180, "نصف سنة": 180, "بعد 6 اشهر": 180,

    # 1 YEAR (365 days)
    "1 year": 365, "one year": 365, "1 yr": 365, "next year": 365, "in a year": 365, "+1 year": 365, "+1y": 365, "annual": 365, "12 months": 365,
    "سنة": 365, "سنه": 365, "عام": 365, "سنة واحدة": 365, "عام واحد": 365, "لسنة": 365, "لسنه": 365, "لعام": 365,
    "لسنة قادمة": 365, "لسنه قادمه": 365, "لعام قادم": 365, "بعد سنة": 365, "بعد سنه": 365, "بعد عام": 365,
    "لمدة سنة": 365, "لمدة عام": 365, "سنة اضافية": 365,

    # 2 YEARS (730 days)
    "2 years": 730, "two years": 730, "2 yrs": 730, "in 2 years": 730, "+2 years": 730, "+2y": 730, "24 months": 730,
    "سنتين": 730, "سنتان": 730, "عامين": 730, "عامان": 730, "لسنتين": 730, "لسنتان": 730, "لعامين": 730,
    "بعد سنتين": 730, "بعد عامين": 730, "لمدة سنتين": 730,
}

ARABIC_MONTHS = {
    "يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4, "أبريل": 4, "مايو": 5, "يونيو": 6,
    "يوليو": 7, "اغسطس": 8, "أغسطس": 8, "سبتمبر": 9, "اكتوبر": 10, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
}

def parse_relative_or_exact_date(text: str, base_date: Optional[date] = None) -> tuple[Optional[date], Optional[int], Optional[str]]:
    """Extracts exact or relative date from prompt."""
    today = base_date or date.today()
    clean = normalize_text(text)

    # 1. ISO format YYYY-MM-DD
    iso_match = re.search(r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", clean)
    if iso_match:
        try:
            d = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            return d, (d - today).days, "iso"
        except ValueError:
            pass

    # 2. DD-MM-YYYY format
    dmy_match = re.search(r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](20\d{2})\b", clean)
    if dmy_match:
        try:
            d = date(int(dmy_match.group(3)), int(dmy_match.group(2)), int(dmy_match.group(1)))
            return d, (d - today).days, "dmy"
        except ValueError:
            pass

    # 3. Relative keywords match
    for phrase, days in sorted(RELATIVE_DAY_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
        norm_phrase = normalize_text(phrase)
        if norm_phrase in clean:
            target = today + timedelta(days=days)
            return target, days, "relative_keyword"

    return None, None, None


def parse_exact_or_colloquial_time(text: str) -> tuple[Optional[time], Optional[str]]:
    """Extracts exact or colloquial time."""
    clean = normalize_text(text)

    # 1. 24-hour HH:MM (e.g. "17:30", "09:15")
    match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", clean)
    if match_24:
        h = int(match_24.group(1))
        m = int(match_24.group(2))
        return time(h, m), "24h_digital"

    # 2. 12-hour with AM/PM or ص/م
    match_12 = re.search(r"\b([1-9]|1[0-2])(?::([0-5]\d))?\s*(am|pm|a\.m\.|p\.m\.|صباحا|مساء|ص|م)\b", clean)
    if match_12:
        h = int(match_12.group(1))
        m = int(match_12.group(2)) if match_12.group(2) else 0
        mer = match_12.group(3).lower()
        if any(p in mer for p in ["pm", "مساء", "م"]) and h < 12:
            h += 12
        elif any(p in mer for p in ["am", "صباحا", "ص"]) and h == 12:
            h = 0
        return time(h, m), "12h_meridiem"

    return None, None


# ==============================================================================
# 3. ENTITY & ID EXTRACTION
# ==============================================================================

ENTITY_PREFIX_PATTERNS = {
    "certificate_id": [
        re.compile(r"\b(?:trn|cert|certificate|شهادة|شهاده|دورة|تدريب)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\btrn[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "incident_id": [
        re.compile(r"\b(?:inc|incident|حادث|بلاغ|اصابة|إصابة)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\binc[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "permit_id": [
        re.compile(r"\b(?:ptw|permit|eptw|تصريح|تصريح عمل)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bptw[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "capa_id": [
        re.compile(r"\b(?:capa|action|اجراء|إجراء|تصحيح)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bcapa[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "inspection_id": [
        re.compile(r"\b(?:insp|inspection|فحص|تفتيش|معاينة)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\binsp[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "jsa_id": [
        re.compile(r"\b(?:jsa|تحليل مهام|سلامة مهام)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bjsa[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "equipment_id": [
        re.compile(r"\b(?:ext|hyd|fire|طفاية|طفايه|معدة|معدة اطفاء)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
    ],
    "employee_id": [
        re.compile(r"\b(?:emp|usr|موظف|عامل|مستخدم)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
        re.compile(r"\bemp[-_]?0*(\d+)\b", re.IGNORECASE),
    ],
    "chemical_id": [
        re.compile(r"\b(?:chem|chemical|مادة|مادة كيميائية)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
    ],
    "sensor_id": [
        re.compile(r"\b(?:sensor|حساس|مستشعر)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
    ],
    "exam_id": [
        re.compile(r"\b(?:exam|فحص طبي|كشف طبي)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
    ],
    "zone_id": [
        re.compile(r"\b(?:zone|area|منطقة|عنبر|قطاع|ورشة)[-_\s#]*0*(\d+)\b", re.IGNORECASE),
    ],
}

def extract_entity_ids(text: str) -> dict[str, int]:
    """Extracts entity IDs (certificate_id, incident_id, permit_id, etc.) from text."""
    results = {}
    if not text:
        return results

    for entity_name, patterns in ENTITY_PREFIX_PATTERNS.items():
        for pat in patterns:
            match = pat.search(text)
            if match:
                try:
                    val = int(match.group(1))
                    if val > 0:
                        results[entity_name] = val
                        break
                except (ValueError, IndexError):
                    pass

    return results


# ==============================================================================
# 4. HSE INTENT CLASSIFICATION ACROSS ALL 15 MODULES
# ==============================================================================

HSE_INTENTS_KEYWORDS = {
    # ── Master Data & Org
    "LIST_DEPARTMENTS": [
        "departments", "list departments", "headcount by department", "show departments", "all departments",
        "الاقسام", "الأقسام", "قائمة الاقسام", "قطاعات المصنع", "هيكل المصنع", "مدراء الاقسام", "عرض الاقسام", "اقسام", "الأقسام", "عنابر", "العنابر", "مناطق", "المناطق", "مصنع"
    ],
    "LIST_ZONES": [
        "plant zones", "list zones", "all zones", "work zones", "show zones",
        "المناطق", "العنابر", "قائمة المناطق", "عنابر الانتاج", "مناطق العمل", "مناطق المصنع", "عرض المناطق", "عنابر", "مناطق", "عنبر"
    ],
    "LIST_EMPLOYEES": [
        "list employees", "all employees", "all workers", "staff list", "personnel list",
        "الموظفين", "العمال", "قائمة الموظفين", "سجل العاملين", "فريق العمل", "عرض الموظفين"
    ],
    "CREATE_EMPLOYEE": [
        "create employee", "add employee", "register worker", "new employee", "hire worker",
        "اضافة موظف", "إضافة موظف", "تسجيل عامل", "اضافة فني", "انشاء موظف", "انشئ موظف", "موظف جديد"
    ],
    "UPDATE_EMPLOYEE": [
        "update employee", "change employee", "transfer worker", "modify employee",
        "تعديل موظف", "تحديث بيانات الموظف", "نقل عامل", "تحديث الموظف"
    ],
    "GET_EMPLOYEE_INFO": [
        "employee info", "worker profile", "who is", "lookup employee", "find worker", "employee card",
        "بيانات الموظف", "ملف الموظف", "معلومات العامل", "استعلام عن موظف", "رقم وظيفي", "بطاقة موظف"
    ],

    # ── Dashboard & KPIs
    "GET_DASHBOARD_SUMMARY": [
        "dashboard", "summary", "safety stats", "overview", "kpis summary", "safe hours", "days without lti",
        "لوحة القيادة", "ملخص السلامة", "احصائيات عامة", "ساعات العمل الآمنة", "أيام بدون إصابات", "مؤشرات الاداء", "داشبورد", "لوحه القياده", "لوحة القياده"
    ],
    "GET_MONTHLY_KPIS": [
        "monthly kpis", "trir", "ltifr", "lost days", "monthly safety trend", "kpi trend",
        "مؤشرات شهرية", "معدل الحوادث", "ساعات العمل الشهرية", "ترير", "تقرير شهري", "مؤشرات الامتثال", "مؤشرات السلامة العامة"
    ],
    "GET_SAFETY_SCORES": [
        "safety scores", "zone compliance", "zone safety rank", "zone scores",
        "تقييم المناطق", "درجات السلامة", "ترتيب العنابر", "نسبة الامتثال", "تقييم عنبر", "درجات العنابر"
    ],
    "LIST_AUDIT_LOGS": [
        "audit log", "audit trail", "system logs", "who changed", "history log",
        "سجل التدقيق", "سجل العمليات", "تاريخ التعديلات", "من قام بالتعديل", "تتبع العمليات"
    ],

    # ── Incidents & Observations
    "CREATE_INCIDENT": [
        "create incident", "report incident", "log incident", "new accident", "near miss", "injury", "spill",
        "بلاغ حادث", "تسجيل حادث", "اصابة عمل", "إصابة عمل", "حادث وشيك", "تسريب", "انسكاب", "حادث حريق", "حادث جديد", "ابلاغ عن حادث"
    ],
    "LOG_SAFETY_OBSERVATION": [
        "log observation", "unsafe act", "unsafe condition", "positive safety observation", "observation",
        "سلوك غير آمن", "حالة غير آمنة", "ملاحظة سلامة", "تسجيل ملاحظة", "تصرف خطر", "ملاحظة"
    ],
    "LIST_INCIDENTS": [
        "list incidents", "show accidents", "active incidents", "recent incidents", "incidents list",
        "قائمة الحوادث", "سجل البلاغات", "عرض الحوادث", "الحوادث المفتوحة", "احصائيات الحوادث", "سجل الحوادث"
    ],
    "GET_INCIDENT_DETAILS": [
        "incident details", "incident investigation", "root cause", "rca", "investigate",
        "تفاصيل الحادث", "تحقيق الحادث", "السبب الجذري", "تقرير الحادث", "تحقيق"
    ],
    "UPDATE_INCIDENT": [
        "update incident", "close incident", "investigate incident", "change incident status",
        "تحديث الحادث", "اغلاق البلاغ", "إغلاق البلاغ", "تعديل حالة الحادث", "انهاء التحقيق"
    ],

    # ── Permits & SIMOPS
    "CREATE_PERMIT": [
        "create permit", "issue permit", "new ptw", "request permit", "hot work permit", "confined space permit",
        "اصدار تصريح", "طلب تصريح عمل", "تصريح عمل ساخن", "تصريح دخول اماكن مغلقة", "انشاء تصريح", "انشئ تصريح", "تصريح جديد"
    ],
    "APPROVE_PERMIT": [
        "approve permit", "sign permit", "validate permit", "authorize ptw", "close permit", "suspend permit",
        "اعتماد تصريح", "الموافقة على التصريح", "توقيع التصريح", "اعتماد تصريح العمل", "اغلاق تصريح", "تعليق تصريح"
    ],
    "LIST_PERMITS": [
        "list permits", "active permits", "show ptw", "open work permits", "permits list",
        "قائمة التصاريح", "تصاريح العمل النشطة", "سجل التصاريح", "عرض تصاريح العمل", "سجل تصاريح", "تصاريح العمل"
    ],
    "GET_PERMIT_DETAILS": [
        "permit details", "ptw gas test", "permit approvals", "ptw checklist",
        "تفاصيل التصريح", "فحص غازات التصريح", "موافقات التصريح", "قائمة فحص التصريح"
    ],
    "CHECK_SIMOPS": [
        "simops", "simultaneous operations", "permit conflicts", "overlapping permits", "conflict", "conflicts",
        "تعارض التصاريح", "العمليات المتزامنة", "تعارض الاعمال", "تضارب تصاريح", "تعارض", "تعارض بين تصاريح", "تضارب"
    ],

    # ── Inspections & Audits
    "SCHEDULE_INSPECTION": [
        "schedule inspection", "routine safety walk", "book safety audit", "schedule walk", "new inspection",
        "جدولة فحص", "تفتيش دوري", "معاينة ميدانية", "جدولة جولة سلامة", "تفتيش جديد", "جدول تفتيش"
    ],
    "LIST_INSPECTIONS": [
        "list inspections", "inspection history", "audit results", "safety walks", "inspections list", "inspections",
        "قائمة التفتيش", "سجل الجولات", "نتائج التفتيش", "سجل المعاينات", "جولات السلامة", "جولات التفتيش", "ملاحظات الفحص", "الفحص المفتوحة", "جولات", "تفتيش"
    ],
    "CREATE_INSPECTION_FINDING": [
        "log finding", "inspection finding", "non-conformance", "audit finding", "finding",
        "تسجيل ملاحظة تفتيش", "ملاحظة عدم مطابقة", "تسجيل مخالفة", "مخالفة تفتيش", "ملاحظة تفتيش"
    ],
    "UPDATE_INSPECTION": [
        "complete inspection", "update inspection", "submit inspection score",
        "انهاء التفتيش", "تحديث نتيجة الفحص", "تسجيل درجة التفتيش", "إغلاق التفتيش"
    ],

    # ── CAPA
    "CREATE_CAPA": [
        "create capa", "new corrective action", "log preventive action", "add capa",
        "اجراء تصحيحي", "إجراء تصحيحي", "اجراء وقائي", "إجراء وقائي", "تسجيل خطة عمل", "انشاء capa", "انشئ capa"
    ],
    "LIST_CAPAS": [
        "list capas", "overdue capas", "open corrective actions", "all capas", "capas list", "capa", "capas",
        "الاجراءات التصحيحية المتأخرة", "قائمة capa", "سجل الاجراءات الوقائية", "خطط العمل", "الاجراءات التصحيحية", "إجراءات capa", "اجراءات capa", "كابا", "المتأخرة", "متأخرة"
    ],
    "UPDATE_CAPA": [
        "update capa", "complete capa", "close corrective action", "verify capa",
        "تحديث الاجراء", "إغلاق الإجراء التصحيحي", "انهاء خطة العمل", "اعتماد الاجراء", "اغلاق capa"
    ],

    # ── Risk Register (HIRA)
    "CREATE_RISK": [
        "create risk", "risk assessment", "hazard identification", "hazard matrix", "new hazard",
        "تقييم مخاطر", "سجل المخاطر", "مصفوفة الخطر", "تحليل سلامة العمل", "تسجيل خطر", "خطر جديد", "اضافة خطر"
    ],
    "LIST_RISK": [
        "list risks", "show risk register", "risk matrix", "high risks", "risks list", "hazards",
        "قائمة المخاطر", "سجل تقييم المخاطر", "مصفوفة المخاطر", "المخاطر العالية", "سجل الخطر"
    ],
    "UPDATE_RISK": [
        "update risk", "modify risk controls", "residual risk",
        "تحديث تقييم المخاطر", "تعديل التحكم", "الخطر المتبقي"
    ],

    # ── Job Safety Analysis (JSA)
    "CREATE_JSA": [
        "create jsa", "new jsa", "job safety analysis", "task risk breakdown",
        "jsa", "تحليل سلامة", "سلامة مهام", "سلامة المهام", "تحليل مهام",
        "تحليل مخاطر", "انشاء jsa", "انشئ jsa", "تحليل سلامة المهام", "تحليل مخاطر العمل", "انشاء تحليل مهام", "انشئ تحليل"
    ],
    "LIST_JSAS": [
        "list jsa", "show jsas", "jsa catalog", "task analysis", "jsas list",
        "قائمة jsa", "سجل تحليل المهام", "نماذج jsa", "تحليلات السلامة", "سجل jsa", "وثائق تحليل سلامة المهام"
    ],
    "UPDATE_JSA": [
        "update jsa", "approve jsa", "modify task controls",
        "تحديث jsa", "اعتماد تحليل المهام", "تعديل اجراءات jsa", "اعتماد jsa"
    ],

    # ── Training & Certifications
    "RENEW_CERTIFICATE": [
        "renew", "renewal", "re-certify", "recertify", "extend certificate", "refresh cert",
        "تجديد", "جدد", "جددها", "تمديد الشهادة", "تجديد شهادة", "مد صلاحية", "اعادة اصدار", "إعادة إصدار"
    ],
    "CREATE_CERTIFICATE": [
        "create certificate", "issue certificate", "new certificate", "add training",
        "اصدار شهادة", "إصدار شهادة", "تسجيل دورة", "اضافة شهادة", "منح شهادة", "شهادة جديدة"
    ],
    "LIST_CERTIFICATES": [
        "list certificates", "show certificates", "training schedule", "matrix", "overdue training", "certificates list",
        "سجل الشهادات", "قائمة الشهادات", "جدول التدريبات", "مصفوفة الكفاءة", "عرض الشهادات", "تدريب منتهي", "شهادات", "الشهادات التدريبية"
    ],
    "CREATE_TRAINING_COURSE": [
        "create course", "add training course", "new course program", "course",
        "اضافة دورة تدريبية", "إنشاء كورس تدريبي", "اضافة برنامج تدريب", "دورة جديدة", "كورس جديد"
    ],

    # ── PPE Management
    "ISSUE_PPE": [
        "issue ppe", "dispense ppe", "give safety helmet", "assign gear", "ppe transaction",
        "صرف مهمات", "صرف خوذة", "صرف حذاء", "صرف قفازات", "تسليم وقاية", "صرف", "اصرف", "مهمات وقاية"
    ],
    "ADD_PPE_ITEM": [
        "add ppe item", "new ppe gear", "register ppe",
        "اضافة مهمة وقاية", "إضافة صنف وقاية", "تسجيل مهمة جديدة", "صنف مهمات جديد"
    ],
    "LIST_PPE": [
        "list ppe", "ppe inventory", "ppe stock", "ppe threshold", "ppe matrix", "ppe list",
        "مخزون المهمات", "رصيد مهمات الوقاية", "مهمات اوشكت على النفاد", "مصفوفة المهمات", "مهمات الوقاية", "حالة مخزون مهمات الوقاية"
    ],
    "UPDATE_PPE_STOCK": [
        "update ppe stock", "restock ppe", "add ppe inventory",
        "تحديث رصيد المهمات", "اضافة مخزون", "توريد مهمات وقاية", "تعديل رصيد مهمات"
    ],

    # ── Fire Safety & Fixed Assets
    "LOG_FIRE_INSPECTION": [
        "log fire inspection", "inspect extinguisher", "check fire hose", "fire audit",
        "فحص طفاية", "تفتيش الحريق", "فحص شبكة الاطفاء", "اختبار الضغط", "فحص دوري لطفايات"
    ],
    "ADD_FIRE_EQUIPMENT": [
        "add fire extinguisher", "new fire equipment", "install extinguisher", "fixed asset",
        "اضافة طفاية", "إضافة طفاية حريق", "تركيب خرطوم اطفاء", "محطة غسيل عيون", "اضافة اصل سلامة", "طفاية جديدة"
    ],
    "LIST_FIRE_EQUIPMENT": [
        "list fire equipment", "expired extinguishers", "fire assets", "eyewash stations", "fire equipment", "fire extinguishers",
        "معدات الحريق", "طفايات منتهية", "صمامات الحريق", "محطات غسيل العيون", "أجهزة الصدمات", "طفايات الحريق", "مطافئ الحريق", "معدات ومطافئ الحريق", "مطافئ", "طفايات"
    ],

    # ── HazMat & Chemicals
    "ADD_CHEMICAL": [
        "add chemical", "register chemical", "new hazardous material", "cas number",
        "اضافة مادة كيميائية", "إضافة مادة", "تسجيل مادة خطرة", "بيانات السلامة الكيميائية", "مادة كيميائية جديدة"
    ],
    "LIST_CHEMICALS": [
        "list chemicals", "chemical inventory", "ghs classes", "hazmat", "chemical compatibility", "chemicals",
        "قائمة المواد الكيميائية", "المواد الخطرة", "توافق المواد الكيميائية", "تصنيفات ghs", "المواد الكيميائية"
    ],

    # ── Occupational Health
    "RECORD_MEDICAL_EXAM": [
        "record medical exam", "schedule medical exam", "fitness for duty", "audiometry", "spirometry", "medical exam",
        "فحص طبي", "كشف طبي", "جدولة كشف دوري", "فحص السمع", "كفاءة طبية", "صلاحية طبية للعمل", "فحص طبي جديد"
    ],
    "LIST_MEDICAL_EXAMS": [
        "list medical exams", "occupational exposure", "noise levels", "dust monitoring", "wearables", "health exams",
        "الفحوصات الطبية", "الصحة المهنية", "قياسات الضوضاء", "التعرض المهني", "الاجهزة الذكية", "سجل الفحوصات الطبية", "الفحوصات الطبية الدورية"
    ],

    # ── AI Vision & IoT
    "ADD_IOT_SENSOR": [
        "add iot sensor", "register sensor", "install sensor", "voc sensor", "new sensor",
        "اضافة حساس", "إضافة مستشعر", "أضف مستشعر", "اضف مستشعر", "أضف حساس", "اضف حساس", "حساس جديد"
    ],
    "LIST_AI_IOT": [
        "iot sensors", "sensor alerts", "ai cameras", "ai events", "vision detections", "ppe violation", "sensors", "iot",
        "حساسات iot", "قراءات الحساسات", "كاميرات الذكاء الاصطناعي", "مخالفات الكاميرا", "كشف عدم ارتداء الخوذة", "انذارات الحساسات", "مستشعرات الغازات", "مستشعرات", "تنبيهات الكاميرات"
    ],

    # ── Security & RAG Knowledge
    "LIST_SECURITY_ROLES": [
        "security roles", "rbac matrix", "user permissions", "integrations",
        "ادوار المستخدمين", "صلاحيات النظام", "مصفوفة الصلاحيات", "التكاملات والربط"
    ],
    "SEARCH_RAG_KNOWLEDGE": [
        "osha standard", "osha", "iso 45001", "iso", "golden rules", "gas limits", "pel", "lel", "confined space rules",
        "معايير السلامة", "مواصفات osha", "ايزو 45001", "القواعد الذهبية", "حدود الغازات", "تعليمات السلامة",
        "اشتراطات", "شروط", "معايير", "مواصفات", "قواعد السلامة", "حدود التعرض"
    ],
}

INTENT_TO_TOOL_MAP = {
    # Master Data
    "LIST_DEPARTMENTS": ["list_departments", "list_zones"],
    "LIST_ZONES": ["list_zones", "list_departments"],
    "LIST_EMPLOYEES": ["list_employees", "get_employee_info"],
    "CREATE_EMPLOYEE": ["create_employee", "list_employees"],
    "UPDATE_EMPLOYEE": ["update_employee", "list_employees"],
    "GET_EMPLOYEE_INFO": ["get_employee_info", "list_certificates"],

    # Dashboard
    "GET_DASHBOARD_SUMMARY": ["get_dashboard_summary", "get_monthly_kpis"],
    "GET_MONTHLY_KPIS": ["get_monthly_kpis", "get_dashboard_summary"],
    "GET_SAFETY_SCORES": ["get_safety_scores", "list_zones"],
    "LIST_AUDIT_LOGS": ["list_audit_logs"],

    # Incidents
    "CREATE_INCIDENT": ["create_incident", "list_incidents"],
    "LOG_SAFETY_OBSERVATION": ["log_safety_observation", "list_incidents"],
    "LIST_INCIDENTS": ["list_incidents", "get_dashboard_summary"],
    "GET_INCIDENT_DETAILS": ["get_incident_details", "get_incident_rca"],
    "UPDATE_INCIDENT": ["update_incident_status", "update_incident"],

    # Permits & SIMOPS
    "CREATE_PERMIT": ["create_permit", "list_permits"],
    "APPROVE_PERMIT": ["update_permit_status", "list_permits"],
    "LIST_PERMITS": ["list_permits", "check_simops_conflicts"],
    "GET_PERMIT_DETAILS": ["get_permit_details", "list_permits"],
    "CHECK_SIMOPS": ["check_simops_conflicts", "list_permits"],

    # Inspections
    "SCHEDULE_INSPECTION": ["schedule_safety_inspection", "list_inspections"],
    "LIST_INSPECTIONS": ["list_inspections", "list_inspection_findings"],
    "CREATE_INSPECTION_FINDING": ["create_inspection_finding", "list_inspection_findings"],
    "UPDATE_INSPECTION": ["update_inspection_status", "list_inspections"],

    # CAPA
    "CREATE_CAPA": ["create_capa", "list_capas"],
    "LIST_CAPAS": ["list_capas", "list_overdue_capas"],
    "UPDATE_CAPA": ["update_capa_status", "list_capas"],

    # Risk & JSA
    "CREATE_RISK": ["create_risk_assessment", "list_risk_register"],
    "LIST_RISK": ["list_risk_register", "get_risk_matrix"],
    "UPDATE_RISK": ["update_risk_assessment", "list_risk_register"],
    "CREATE_JSA": ["create_jsa", "list_jsas"],
    "LIST_JSAS": ["list_jsas", "get_jsa_details"],
    "UPDATE_JSA": ["update_jsa", "list_jsas"],

    # Training
    "RENEW_CERTIFICATE": ["update_certificate_status", "update_certificate", "list_certificates"],
    "CREATE_CERTIFICATE": ["create_certificate", "list_training_courses"],
    "LIST_CERTIFICATES": ["list_certificates", "get_overdue_training"],
    "CREATE_TRAINING_COURSE": ["create_training_course", "list_training_courses"],

    # PPE
    "ISSUE_PPE": ["create_ppe_transaction", "get_ppe_stock_status", "list_ppe_inventory"],
    "ADD_PPE_ITEM": ["add_ppe_item", "list_ppe_inventory"],
    "LIST_PPE": ["list_ppe_inventory", "get_ppe_stock_status", "list_ppe_matrix"],
    "UPDATE_PPE_STOCK": ["update_ppe_stock", "list_ppe_inventory"],

    # Fire Safety
    "LOG_FIRE_INSPECTION": ["log_fire_inspection", "list_fire_equipment"],
    "ADD_FIRE_EQUIPMENT": ["add_fire_equipment", "add_fixed_safety_asset", "list_fire_equipment"],
    "LIST_FIRE_EQUIPMENT": ["list_fire_equipment", "get_expired_fire_equipment", "list_fixed_safety_assets"],

    # Chemicals
    "ADD_CHEMICAL": ["add_chemical", "list_chemicals"],
    "LIST_CHEMICALS": ["list_chemicals", "get_chemical_compatibility"],

    # Occupational Health
    "RECORD_MEDICAL_EXAM": ["record_medical_exam", "schedule_medical_exam", "list_medical_exams"],
    "LIST_MEDICAL_EXAMS": ["list_medical_exams", "list_occupational_exposures", "list_wearable_devices"],

    # AI & IoT
    "ADD_IOT_SENSOR": ["add_iot_sensor", "list_iot_sensors"],
    "LIST_AI_IOT": ["list_iot_sensors", "get_recent_sensor_alerts", "list_cameras", "get_recent_ai_events"],

    # Security & RAG
    "LIST_SECURITY_ROLES": ["list_security_roles", "list_integrations"],
    "SEARCH_RAG_KNOWLEDGE": ["search_hse_knowledge"],
}

def classify_hse_intent(text: str) -> tuple[Optional[str], list[str]]:
    """Classifies user prompt into primary and secondary HSE intents."""
    clean = normalize_text(text)
    tokens = set(extract_word_tokens(text))
    matched = []

    for intent, keywords in HSE_INTENTS_KEYWORDS.items():
        score = 0
        for kw in keywords:
            norm_kw = normalize_text(kw)
            if " " in norm_kw:
                if norm_kw in clean:
                    score += len(norm_kw.split()) * 3
            else:
                if norm_kw in tokens:
                    score += 2
                elif norm_kw in clean:
                    score += 1
        if score > 0:
            matched.append((intent, score))

    if not matched:
        return None, []

    matched.sort(key=lambda x: x[1], reverse=True)
    primary = matched[0][0]
    all_intents = [m[0] for m in matched]
    return primary, all_intents


# ==============================================================================
# 5. UNIFIED PARSED HSE PROMPT DATACLASS & ENGINE
# ==============================================================================

@dataclass
class ParsedHsePrompt:
    raw_prompt: str
    normalized_prompt: str
    primary_intent: Optional[str] = None
    all_intents: list[str] = field(default_factory=list)
    recommended_tools: list[str] = field(default_factory=list)
    entity_ids: dict[str, int] = field(default_factory=dict)
    target_date: Optional[date] = None
    target_time: Optional[time] = None
    target_datetime: Optional[datetime] = None
    days_delta: Optional[int] = None
    date_match_type: Optional[str] = None
    time_match_type: Optional[str] = None
    is_crud_mutation: bool = False
    status_target: Optional[str] = None


def parse_user_hse_prompt(text: str, base_date: Optional[date] = None) -> ParsedHsePrompt:
    """Comprehensive parsing engine for HSE user prompts."""
    today = base_date or date.today()
    norm = normalize_text(text)

    # 1. Intent Classification
    primary_intent, all_intents = classify_hse_intent(text)

    # 2. Entity IDs
    entity_ids = extract_entity_ids(text)

    # 3. Date & Time Parsing
    target_date, days_delta, date_type = parse_relative_or_exact_date(text, base_date=today)
    target_time, time_type = parse_exact_or_colloquial_time(text)

    target_datetime = None
    resolved_d = target_date or today
    resolved_t = target_time or time(23, 59)
    if target_date or target_time:
        target_datetime = datetime.combine(resolved_d, resolved_t)

    # 4. Mutation check
    mutation_keywords = [
        "renew", "تجديد", "جدد", "تمديد", "تعديل", "تحديث", "تغيير", "update", "modify",
        "صرف", "انشئ", "أنشئ", "سجل", "أضف", "اضف", "create", "add", "issue", "approve", "اعتمد", "احذف", "delete", "cancel", "الغاء", "إلغاء"
    ]
    is_crud = any(k in norm for k in mutation_keywords)

    # 5. Status Target
    status_target = None
    if any(k in norm for k in ["valid", "سارية", "ساريه", "تجديد", "renew", "تفعيل", "معتمدة"]):
        status_target = "VALID"
    elif any(k in norm for k in ["expired", "منتهية", "منتهيه", "انهاء", "إنهاء", "الغاء", "إلغاء"]):
        status_target = "EXPIRED"
    elif any(k in norm for k in ["approve", "approved", "اعتماد", "معتمد"]):
        status_target = "APPROVED"

    # 6. Tool Recommendation
    tools = []
    if primary_intent and primary_intent in INTENT_TO_TOOL_MAP:
        tools.extend(INTENT_TO_TOOL_MAP[primary_intent])
    for intent in all_intents[1:]:
        if intent in INTENT_TO_TOOL_MAP:
            for t in INTENT_TO_TOOL_MAP[intent]:
                if t not in tools:
                    tools.append(t)

    return ParsedHsePrompt(
        raw_prompt=text,
        normalized_prompt=norm,
        primary_intent=primary_intent,
        all_intents=all_intents,
        recommended_tools=tools,
        entity_ids=entity_ids,
        target_date=target_date,
        target_time=target_time,
        target_datetime=target_datetime,
        days_delta=days_delta,
        date_match_type=date_type,
        time_match_type=time_type,
        is_crud_mutation=is_crud,
        status_target=status_target,
    )


def get_recommended_tools_for_prompt(text: str, all_tools: list[dict]) -> list[dict]:
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
        fallback_names = ["get_dashboard_summary", "list_incidents", "list_permits", "list_inspections", "search_hse_knowledge", "run_read_only_query"]
        for fn in fallback_names:
            if fn in tool_map and tool_map[fn] not in selected:
                selected.append(tool_map[fn])

    return selected
