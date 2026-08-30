"""
ESCA HSE AI Agent - UI Button Automation Keywords & Action Library
Dedicated NLP lexicon and entity extractor for all interactive buttons across
the Incident Register, Root Cause Analysis, External Reporting Templates, and Safety Dashboard.
"""

from typing import Dict, List, Any, Optional
import re

# ── 1. EXCEL EXPORT LEXICON ──────────────────────────────────────────────────
EXCEL_EXPORT_KEYWORDS = [
    # Arabic
    "تصدير excel", "تصدير اكسل", "تصدير الإكسل", "تصدير ملف excel", "تصدير ملف اكسل",
    "تصدير الحوادث إلى excel", "تصدير الحوادث لاكسل", "تصدير الحوادث لاكسيل", "تصدير سجل الحوادث",
    "تصدير سجل الحوادث اكسل", "تصدير سجل الحوادث excel", "تحميل ملف excel للحوادث",
    "تحميل اكسل", "تنزيل اكسل", "تصدير السجل", "شيت اكسل الحوادث", "تقرير الحوادث excel",
    "تصدير الحوادث إلى ملف excel", "تصدير لملف إكسل", "استخراج اكسل", "تصدير جدول الحوادث",
    "تصدير كل الحوادث excel", "تحميل شيت الحوادث", "تصدير بيانات الحوادث",
    # English
    "export excel", "export to excel", "export incidents to excel", "export incidents excel",
    "download excel", "download incidents spreadsheet", "export incident register",
    "export to xlsx", "generate excel report", "dump incidents to excel", "download incident log excel",
    "export incident sheet", "save incidents as excel"
]

# ── 2. EXTERNAL STATUTORY REPORT TEMPLATES LEXICON ────────────────────────────
EXTERNAL_TEMPLATES_KEYWORDS = [
    # Labor Office (قانون العمل 12 لسنة 2003)
    "توليد نموذج مكتب العمل", "نموذج مكتب العمل", "إخطار إصابة عمل مكتب العمل", "إخطار مكتب العمل",
    "استمارة مكتب العمل", "نموذج إصابة مكتب العمل", "بلاغ مكتب العمل", "إخطار مكتب العمل بإصابة",
    "توليد نموذج مكتب العمل — إخطار إصابة", "توليد نموذج مكتب العمل لاخطار اصابة", "نموذج القوى العاملة",
    "labor office form", "labor office injury notice", "generate labor office report", "ministry of labor form",

    # Social Insurance (قانون التأمينات 148 لسنة 2019)
    "توليد نموذج التأمينات", "توليد نموذج التأمينات الاجتماعية", "نموذج التأمينات الاجتماعية",
    "استمارة 1 إصابات", "استمارة 1 اصابات", "إخطار التأمينات الاجتماعية", "إخطار التأمينات",
    "استمارة إصابة التأمينات", "نموذج التأمين الاجتماعي", "توليد استمارة التأمينات",
    "social insurance form", "social insurance injury notice", "generate social insurance report",

    # Insurance Company Claim
    "توليد مطالبة التأمين", "مطالبة شركة التأمين", "مطالبة التأمين", "إخطار شركة التأمين للحادث",
    "مطالبة تأمين الحادث", "تقرير شركة التأمين", "مطالبة تعويض الحادث", "توليد مطالبة شركة التأمين",
    "insurance claim", "insurance company claim", "generate insurance claim", "insurance claim form",

    # Environmental Agency EEAA (قانون البيئة 4 لسنة 1994)
    "توليد إخطار جهاز شؤون البيئة", "إخطار جهاز شؤون البيئة", "إخطار جهاز شئون البيئة",
    "إخطار البيئة", "إخطار شؤون البيئة", "بلاغ شؤون البيئة", "تقرير جهاز البيئة",
    "إخطار جهاز شؤون البيئة عن الحادث", "بلاغ بيئي", "تقرير الحادث البيئي",
    "environmental agency notification", "eeaa environmental report", "generate environmental notification",

    # General templates category
    "قوالب الإبلاغ الخارجي", "قوالب الابلاغ الخارجي", "توليد قوالب الإبلاغ الخارجي", "النماذج الخارجية",
    "statutory external templates", "external compliance forms", "government hse forms"
]

# ── 3. ROOT CAUSE ANALYSIS & RCA LEXICON ─────────────────────────────────────
RCA_MANAGE_KEYWORDS = [
    # Specific RCA creation & management
    "تحليل السبب الجذري", "سجل تحليل السبب الجذري", "تحليل rca", "إضافة تحليل السبب الجذري",
    "توثيق rca", "تسجيل تحليل rca", "سجل rca", "السبب الجذري للحادث", "توثيق السبب الجذري",
    "تحليل السبب الجذري للحادث", "5 whys", "5-whys", "طريقة 5 لماذا", "fishbone", "عظم السمكة",
    "إيشيكاوا", "ishikawa", "root cause analysis", "create rca", "record root cause",

    # YTD RCA Summary
    "تحليل الأسباب الجذرية — ytd", "تحليل الأسباب الجذرية ytd", "تحليل الاسباب الجذرية ytd",
    "الأسباب الجذرية الأكثر تكراراً", "الاسباب الجذرية الاكثر تكرارا", "نسب أسباب الحوادث",
    "إحصائيات أسباب الحوادث", "ملخص الأسباب الجذرية", "root causes ytd", "root cause breakdown",
    "top root causes", "ytd root cause analysis"
]

# ── 4. DASHBOARD REFRESH LEXICON ─────────────────────────────────────────────
DASHBOARD_REFRESH_KEYWORDS = [
    # Arabic
    "تحديث", "حدث", "تحديث لوحة القيادة", "تحديث لوحه القياده", "تحديث البيانات",
    "تحديث الإحصائيات", "تحديث الاحصائيات", "إعادة تحميل لوحة القيادة", "تحديث مؤشرات السلامة",
    "تحديث الداشبورد", "تحديث شامل", "حدث لوحة القيادة", "حدث البيانات", "تحديث مباشر",
    "إعادة حساب المؤشرات", "تحديث شاشة القيادة", "تحديث لوحة السلامة",
    # English
    "refresh dashboard", "refresh stats", "refresh safety metrics", "reload dashboard",
    "reload dashboard data", "recalculate safety scores", "update dashboard", "refresh all stats",
    "sync dashboard", "live refresh"
]

# ── 5. INCIDENT FILTERING & SEARCH LEXICON ───────────────────────────────────
INCIDENT_FILTER_KEYWORDS = [
    # Open filter
    "الحوادث المفتوحة", "البلاغات المفتوحة", "اعرض الحوادث المفتوحة", "فلترة الحوادث على المفتوح",
    "فلتر المفتوح", "حوادث مفتوحة", "show open incidents", "filter open incidents", "list open incidents",

    # Investigating filter
    "الحوادث تحت التحقيق", "البلاغات تحت التحقيق", "اعرض الحوادث تحت التحقيق", "تحت التحقيق",
    "فلتر تحت التحقيق", "show investigating incidents", "filter investigating",

    # Closed filter
    "الحوادث المغلقة", "البلاغات المغلقة", "اعرض الحوادث المغلقة", "فلترة الحوادث المغلقة",
    "فلتر المغلق", "حوادث مغلقة", "show closed incidents", "filter closed incidents",

    # All filter
    "جميع الحوادث", "كل الحوادث", "فلتر الكل", "عرض كل الحوادث", "show all incidents"
]


def extract_template_type_from_text(text: str) -> Optional[str]:
    """Resolves template type code ('LABOR_OFFICE', 'SOCIAL_INSURANCE', 'INSURANCE_CLAIM', 'ENVIRONMENTAL_AGENCY') from user query."""
    t_lower = text.lower()
    if any(w in t_lower for w in ["مكتب العمل", "قوى عاملة", "قانون العمل", "labor office", "ministry of labor"]):
        return "LABOR_OFFICE"
    if any(w in t_lower for w in ["تأمينات اجتماعية", "تأمينات", "تأمين اجتماعي", "استمارة 1", "social insurance"]):
        return "SOCIAL_INSURANCE"
    if any(w in t_lower for w in ["مطالبة", "شركة التأمين", "وثيقة التأمين", "تعويض", "insurance claim", "policy claim"]):
        return "INSURANCE_CLAIM"
    if any(w in t_lower for w in ["بيئة", "شؤون البيئة", "شئون البيئة", "eeaa", "environmental", "جهاز البيئة", "تسريب بيئي"]):
        return "ENVIRONMENTAL_AGENCY"
    return "LABOR_OFFICE"


def extract_filter_target_from_text(text: str) -> Optional[str]:
    """Resolves filter target ('open', 'investigating', 'closed', 'all') from user query."""
    t_lower = text.lower()
    if any(w in t_lower for w in ["مفتوح", "مفتوحة", "open", "نشطة"]):
        return "open"
    if any(w in t_lower for w in ["تحت التحقيق", "تحقيق", "investigating", "under investigation"]):
        return "investigating"
    if any(w in t_lower for w in ["مغلق", "مغلقة", "منتهية", "closed", "resolved"]):
        return "closed"
    if any(w in t_lower for w in ["الكل", "كل", "جميع", "all"]):
        return "all"
    return None
