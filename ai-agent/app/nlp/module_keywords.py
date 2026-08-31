"""
ESCA HSE AI Agent - Massive Multilingual Keyword Library Across All 15 Modules

Organizes enterprise HSE vocabulary, colloquial dialects (Egyptian & Gulf),
formal Arabic (MSA), and English industry standards across all 15 HSE modules.
"""

from typing import Dict, List, Any, Optional
from .normalization import normalize_text


# ==============================================================================
# 1. MODULE METADATA DIRECTORY (All 15 Modules)
# ==============================================================================

MODULE_METADATA: Dict[int, Dict[str, Any]] = {
    1: {
        "module_code": "MASTER_DATA",
        "name_en": "Core Master Data & Organization Structure",
        "name_ar": "البيانات الأساسية والهيكل التنظيمي",
        "primary_tables": ["departments", "zones", "employees"],
        "description": "Plant hierarchy, departments, production lines, zones, headcount, and worker directories."
    },
    2: {
        "module_code": "DASHBOARD_KPIS",
        "name_en": "Executive Safety Dashboard & KPI Analytics",
        "name_ar": "لوحة القيادة التنفيذية ومؤشرات الأداء",
        "primary_tables": ["monthly_kpis", "audit_logs"],
        "description": "TRIR, LTIFR, safe man-hours, compliance rankings, zone scores, and executive metrics."
    },
    3: {
        "module_code": "INCIDENTS_OBSERVATIONS",
        "name_en": "Incidents, Near Misses & Safety Observations",
        "name_ar": "الحوادث، الحوادث الوشيكة، وملاحظات السلامة",
        "primary_tables": ["incidents", "observations"],
        "description": "Workplace injuries, chemical spills, fires, near misses, unsafe acts, unsafe conditions, and RCA."
    },
    4: {
        "module_code": "EPTW_SIMOPS",
        "name_en": "Electronic Permit to Work (ePTW) & SIMOPS",
        "name_ar": "تصاريح العمل الإلكترونية وإدارة العمليات المتزامنة",
        "primary_tables": ["permits"],
        "description": "Hot work, cold work, confined space, heights, LOTO, excavation, lifting permits, and SIMOPS conflict analysis."
    },
    5: {
        "module_code": "INSPECTIONS_AUDITS",
        "name_en": "Safety Inspections, Field Audits & Checklists",
        "name_ar": "التفتيش الميداني، الجولات التفقدية، ونماذج الفحص",
        "primary_tables": ["inspections", "findings"],
        "description": "Safety walks, scheduled audits, dynamic checklists, non-conformance findings, and scoring."
    },
    6: {
        "module_code": "CAPA_MANAGEMENT",
        "name_en": "Corrective and Preventive Actions (CAPA)",
        "name_ar": "الإجراءات التصحيحية والوقائية (CAPA)",
        "primary_tables": ["capas"],
        "description": "Action items, overdue remediation plans, root cause eradication, and implementation verification."
    },
    7: {
        "module_code": "HIRA_RISK_REGISTER",
        "name_en": "Hazard Identification & Risk Assessment (HIRA)",
        "name_ar": "تقييم وتحديد المخاطر وسجل المخاطر (HIRA)",
        "primary_tables": ["risk_register"],
        "description": "5x5 risk matrices, likelihood, severity, inherent vs residual risk, and hierarchy of controls."
    },
    8: {
        "module_code": "JSA_JHA",
        "name_en": "Job Safety Analysis (JSA / JHA)",
        "name_ar": "تحليل سلامة المهام وبيان طريقة العمل الآمنة",
        "primary_tables": ["jsa"],
        "description": "Step-by-step task breakdown, job hazards, required safety controls, and PPE mapping."
    },
    9: {
        "module_code": "TRAINING_COMPETENCY",
        "name_en": "HSE Training, Certifications & Competency",
        "name_ar": "التدريب والسلامة المهنية ومصفوفة الكفاءة",
        "primary_tables": ["certificates", "training_courses"],
        "description": "OSHA 30hr, First Aid, Firefighting, LOTO certifications, renewal workflows, and validity alerts."
    },
    10: {
        "module_code": "PPE_MANAGEMENT",
        "name_en": "Personal Protective Equipment (PPE) & Inventory",
        "name_ar": "إدارة مهمات الوقاية الشخصية ومخزون السلامة",
        "primary_tables": ["ppe_inventory", "ppe_transactions", "ppe_matrix"],
        "description": "Safety helmets, glasses, gloves, boots, harnesses, stock balances, reorder points, and dispensing."
    },
    11: {
        "module_code": "FIRE_SAFETY_ASSETS",
        "name_en": "Fire Safety, Extinguishers & Fixed Emergency Assets",
        "name_ar": "أنظمة ومعدات الإطفاء، محطات غسيل العيون، وأصول الطوارئ",
        "primary_tables": ["fire_equipment", "fire_inspections", "fixed_safety_assets"],
        "description": "DCP/CO2/Foam extinguishers, hydrants, eyewash stations, AEDs, first aid stations, and QR inspection."
    },
    12: {
        "module_code": "HAZMAT_CHEMICALS",
        "name_en": "HazMat, Chemical Inventory & GHS Compatibility",
        "name_ar": "المواد الكيميائية الخطرة، صحائف السلامة (SDS)، والتوافق",
        "primary_tables": ["chemicals"],
        "description": "CAS numbers, GHS pictograms, flammables, acids, solvents, gases, bunded storage, and compatibility."
    },
    13: {
        "module_code": "OCCUPATIONAL_HEALTH",
        "name_en": "Occupational Health, Industrial Hygiene & Medical",
        "name_ar": "الصحة المهنية، الفحوصات الطبية، والقياسات البيئية",
        "primary_tables": ["wearable_devices", "wearable_events"],
        "description": "Periodic medical checkups, audiometry, spirometry, noise dosimetry, heat stress, and dust monitoring."
    },
    14: {
        "module_code": "AI_IOT_TELEMETRY",
        "name_en": "AI Vision Detection & IoT Sensor Telemetry",
        "name_ar": "كاميرات الذكاء الاصطناعي ومستشعرات إنترنت الأشياء",
        "primary_tables": ["iot_sensors", "sensor_readings", "cameras", "ai_events"],
        "description": "Gas sensors (LEL, H2S, CO, O2), PPE violation vision AI, man-down detection, and real-time telemetry."
    },
    15: {
        "module_code": "GOVERNANCE_RAG_SECURITY",
        "name_en": "HSE Governance, OSHA/ISO Standards & RBAC Security",
        "name_ar": "حوكمة السلامة، معايير OSHA/ISO، والمكتبة المعرفية",
        "primary_tables": ["qa_sessions", "qa_messages", "qa_tool_calls"],
        "description": "OSHA 1910/1926, ISO 45001, Egyptian Labor Law 12/2003, Golden Rules, and RBAC permissions."
    },
}


# ==============================================================================
# 2. COMPREHENSIVE INTENTS & KEYWORD LEXICONS ACROSS ALL 15 MODULES
# ==============================================================================

HSE_INTENTS_KEYWORDS: Dict[str, List[str]] = {
    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 1: MASTER DATA & ORGANIZATION
    # ══════════════════════════════════════════════════════════════════════════
    "LIST_DEPARTMENTS": [
        "departments", "list departments", "headcount by department", "show departments", "all departments",
        "plant layout", "factory sectors", "organizational chart", "org structure", "departments list",
        "الاقسام", "الأقسام", "قائمة الاقسام", "قطاعات المصنع", "هيكل المصنع", "مدراء الاقسام", "عرض الاقسام",
        "اقسام", "عنابر", "العنابر", "مناطق", "المناطق", "مصنع", "اقسام المصنع", "هيكل الشركة", "قطاعات الإنتاج"
    ],
    "GET_DEPARTMENT_DETAILS": [
        "department details", "department profile", "department zones", "department manager",
        "تفاصيل القسم", "بيانات القسم", "معلومات القسم", "مدير القسم", "عنابر القسم"
    ],
    "GET_DEPARTMENT_ZONES_SUMMARY": [
        "department zones summary", "zones by department", "zones per department", "sectors zones breakdown",
        "ملخص المناطق لكل قسم", "ملخص المناطق", "توزيع المناطق على الاقسام", "سعة الأقسام والمناطق"
    ],
    "CREATE_DEPARTMENT": [
        "create department", "add department", "new department", "register sector",
        "اضافة قسم", "إضافة قسم جديد", "انشاء قطاع", "تسجيل قسم جديد"
    ],
    "UPDATE_DEPARTMENT": [
        "update department", "modify department", "edit department",
        "تعديل قسم", "تحديث بيانات القسم", "تغيير اسم القسم"
    ],
    "DELETE_DEPARTMENT": [
        "delete department", "remove department",
        "حذف قسم", "مسح قسم"
    ],
    "LIST_ZONES": [
        "plant zones", "list zones", "all zones", "work zones", "show zones", "production areas",
        "cable plant lines", "substations", "chemical stores", "drum yard", "copper drawing line",
        "المناطق", "العنابر", "قائمة المناطق", "عنابر الانتاج", "مناطق العمل", "مناطق المصنع", "عرض المناطق",
        "عنبر", "منطقة", "خطوط الانتاج", "عنابر الكابلات", "ساحة الطبول", "محطة الكهرباء", "المستودع الرئيسي"
    ],
    "GET_ZONE_DETAILS": [
        "zone details", "zone profile", "zone capacity", "fire equipment in zone",
        "تفاصيل المنطقة", "بيانات العنبر", "معلومات المنطقة", "سعة المنطقة", "معدات الحريق في المنطقة"
    ],
    "CREATE_ZONE": [
        "create zone", "add zone", "new zone", "register zone", "add production zone", "create area", "new area",
        "إضافة منطقة", "اضافة منطقة", "إنشاء منطقة", "انشاء منطقة", "منطقة جديدة", "أضف منطقة", "اضف منطقة",
        "تسجيل منطقة", "عنبر جديد", "أضف عنبر", "اضف عنبر", "إضافة عنبر", "اضافة عنبر", "انشاء عنبر جديد"
    ],
    "UPDATE_ZONE": [
        "update zone", "modify zone", "edit zone", "change zone occupancy", "rename zone",
        "تعديل منطقة", "تحديث المنطقة", "تعديل سعة المنطقة", "تغيير اسم المنطقة", "تحديث بيانات المنطقة"
    ],
    "DELETE_ZONE": [
        "delete zone", "remove zone", "deactivate zone",
        "حذف منطقة", "إلغاء منطقة", "الغاء منطقة", "مسح منطقة", "امسح منطقة", "حذف عنبر"
    ],
    "LIST_EMPLOYEES": [
        "list employees", "all employees", "all workers", "staff list", "personnel list", "worker directory",
        "technicians list", "safety officers list", "supervisors roster", "active workforce",
        "الموظفين", "العمال", "قائمة الموظفين", "سجل العاملين", "فريق العمل", "عرض الموظفين", "العاملين",
        "الفنيين", "سجل العمال", "فريق السلامة", "قائمة العمال", "دليل الموظفين", "طاقم العمل", "قائمة الفنيين"
    ],
    "CREATE_EMPLOYEE": [
        "create employee", "add employee", "register worker", "new employee", "hire worker", "onboard employee",
        "add technician", "register operator", "new safety officer", "add worker", "register technician",
        "اضافة موظف", "إضافة موظف", "تسجيل عامل", "اضافة فني", "انشاء موظف", "انشئ موظف", "موظف جديد",
        "أضف موظف", "اضف موظف", "تسجيل موظف جديد", "تعيين عامل", "إضافة فني جديد", "انشاء سجل موظف",
        "أضف فني", "اضف فني", "فني جديد", "أضف عامل", "اضف عامل", "عامل جديد", "تسجيل فني جديد", "تعيين فني"
    ],
    "UPDATE_EMPLOYEE": [
        "update employee", "change employee", "transfer worker", "modify employee", "edit employee",
        "change department", "change job title", "promote worker", "reassign employee",
        "تعديل موظف", "تحديث بيانات الموظف", "نقل عامل", "تحديث الموظف", "تغيير قسم الموظف", "تعديل المسمى الوظيفي",
        "ترقية عامل", "تحديث بيانات العامل", "تعديل وظيفة", "نقل الموظف إلى"
    ],
    "GET_EMPLOYEE_INFO": [
        "employee info", "worker profile", "who is", "lookup employee", "find worker", "employee card",
        "employee details", "worker records", "employee certifications",
        "بيانات الموظف", "ملف الموظف", "معلومات العامل", "استعلام عن موظف", "رقم وظيفي", "بطاقة موظف",
        "تفاصيل الموظف", "سجل الموظف", "معلومات الفني", "بيانات العامل", "من هو الموظف"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 2: DASHBOARD, METRICS & KPIS
    # ══════════════════════════════════════════════════════════════════════════
    "GET_DASHBOARD_SUMMARY": [
        "dashboard", "summary", "safety stats", "overview", "kpis summary", "safe hours", "days without lti",
        "executive briefing", "safety scorecard", "zero harm metrics", "safety performance",
        "executive safety dashboard", "safety overview", "plant safety metrics",
        "لوحة القيادة", "ملخص السلامة", "احصائيات عامة", "ساعات العمل الآمنة", "أيام بدون إصابات", "مؤشرات الاداء",
        "داشبورد", "لوحه القياده", "لوحة القياده", "تقرير السلامة العام", "مؤشرات السلامة العامة", "احصائيات المصنع"
    ],
    "REFRESH_DASHBOARD": [
        "تحديث", "حدث", "تحديث لوحة القيادة", "تحديث لوحه القياده", "تحديث البيانات",
        "تحديث الإحصائيات", "تحديث الاحصائيات", "إعادة تحميل لوحة القيادة", "تحديث مؤشرات السلامة",
        "تحديث الداشبورد", "تحديث شامل", "حدث لوحة القيادة", "حدث البيانات", "تحديث مباشر",
        "إعادة حساب المؤشرات", "تحديث شاشة القيادة", "تحديث لوحة السلامة",
        "refresh dashboard", "refresh stats", "refresh safety metrics", "reload dashboard",
        "reload dashboard data", "recalculate safety scores", "update dashboard", "refresh all stats",
        "sync dashboard", "live refresh"
    ],
    "GET_MONTHLY_KPIS": [
        "monthly kpis", "trir", "ltifr", "ltisr", "lost days", "monthly safety trend", "kpi trend", "osha 300 log",
        "frequency rate", "severity rate", "incident rate formula", "near miss rate",
        "مؤشرات شهرية", "معدل الحوادث", "ساعات العمل الشهرية", "ترير", "تقرير شهري", "مؤشرات الامتثال",
        "معدل تكرار الإصابات", "معدل شدة الإصابات", "أيام العمل الضائعة", "معدل الحوادث الشهري", "ltifr"
    ],
    "GET_SAFETY_SCORES": [
        "safety scores", "zone compliance", "zone safety rank", "zone scores", "plant safety index",
        "تقييم المناطق", "درجات السلامة", "ترتيب العنابر", "نسبة الامتثال", "تقييم عنبر", "درجات العنابر",
        "ترتيب المناطق الأكثر أمانا", "مؤشر سلامة العنابر", "تقييم خطوط الإنتاج"
    ],
    "LIST_AUDIT_LOGS": [
        "audit log", "audit trail", "system logs", "who changed", "history log", "transaction logs", "user activity",
        "سجل التدقيق", "سجل العمليات", "تاريخ التعديلات", "من قام بالتعديل", "تتبع العمليات", "سجل النشاطات", "تعديلات النظام"
    ],
    "EXPORT_REPORTS_EXCEL": [
        "تصدير تقرير الإكسل", "تصدير تقرير السلامة excel", "تصدير تقرير التقارير والتحليلات", "تصدير مصنف التقارير",
        "تصدير شيت السلامة", "تصدير المؤشرات excel", "تصدير تقرير الإكسيل التنفيذي", "تصدير تقرير الايكسل",
        "تصدير مصنف الإكسيل", "تصدير التقارير إكسل", "تصدير التقارير excel", "تحميل شيت تقرير السلامة",
        "تصدير تقرير إكسل", "تصدير تقرير اكسل", "تصدير تقرير excel", "تصدير مصنف excel", "مصنف الإكسيل",
        "export reports excel", "export executive report excel", "download executive workbook", "export reports to excel",
        "export analytics excel", "download hse report xlsx", "export safety workbook excel", "export report to excel",
        "export executive report", "export hse excel"
    ],
    "EXPORT_REPORTS_PDF": [
        "تصدير pdf", "طباعة التقرير", "تصدير تقرير السلامة pdf", "طباعة تقرير المؤشرات", "تصدير بي دي اف",
        "تصدير بي دي إف", "طباعة التقرير التنفيذي", "تصدير التقرير التنفيذي pdf", "تصدير التقارير pdf",
        "اطبع التقرير", "اطبع تقرير", "اطبع التقرير التنفيذي", "اطبع pdf", "طباعة pdf", "تصدير ملف pdf",
        "تقرير pdf للسلامة", "تقرير pdf", "اطبع تقرير السلامة", "اطبع التقرير التنفيذي pdf",
        "export pdf", "print report", "print executive report", "export reports to pdf", "download pdf report",
        "print hse report", "print executive pdf", "export executive pdf", "generate pdf report"
    ],
    "SEND_REPORT_TO_MANAGEMENT": [
        "إرسال للإدارة", "إرسال التقرير للإدارة", "ارسل التقرير للادارة العليا", "إرسال تقرير السلامة للإدارة",
        "إرسال التقرير التنفيذي للإدارة العليا", "ارسل تقرير السلامة", "إرسال التقرير للمدير", "ارسل للإدارة",
        "ارسال للادارة", "ارسال التقرير للإدارة التنفيذية", "إرسال للإدارة العليا", "إرسال ملخص السلامة للإدارة",
        "ارسل تقرير السلامة للإدارة العليا", "ارسل تقرير السلامة للإدارة", "ارسل التقرير للإدارة",
        "إرسال للإدارة التنفيذية", "ارسال للإدارة العليا", "إرسال التقرير", "ارسل التقرير",
        "send report to management", "send to management", "dispatch report to leadership", "send executive report",
        "dispatch safety report", "submit report to management", "send safety report to management"
    ],
    "GENERATE_CUSTOM_REPORT": [
        "توليد تقرير مخصص", "مولد التقارير", "توليد الآن", "انشئ تقرير مخصص", "تقرير مخصص للحوادث",
        "تقرير مخصص للتصاريح", "تقرير مخصص للتفتيش", "تقرير مخصص للحريق", "توليد تقرير فوري",
        "مولد التقارير المخصص", "توليد تقرير", "توليد الان", "تقرير مخصص", "انشاء تقرير مخصص",
        "توليد تقرير مخصص عن تصاريح العمل", "توليد تقرير مخصص عن الحوادث", "تقرير مخصص عن التصاريح",
        "generate custom report", "ad hoc report builder", "build custom report", "generate custom hse report",
        "ad-hoc report", "custom report builder", "generate ad hoc report", "generate custom report for permits"
    ],
    "OPEN_READY_REPORT": [
        "التقارير الجاهزة للتوليد", "التقارير الجاهزة", "افتح التقرير الشهري", "عرض التقرير الشهري",
        "تقرير تحليل الحوادث", "تقرير جاهزية الحريق", "مصفوفة الكفاءات والتدريب", "سجل المخاطر المحدث",
        "سجل المخاطر المحدّث", "حزمة التدقيق iso 45001", "حزمة التدقيق أيزو 45001", "حزمة تدقيق iso",
        "افتح تقرير جاهزية الحريق", "افتح حزمة تدقيق iso 45001", "عرض تقرير الكفاءات والتدريب",
        "عرض تقرير سجل المخاطر", "افتح تقرير الحوادث", "التقرير الشهري للسلامة", "تقرير جاهزية الطوارئ",
        "open ready report", "open monthly hse report", "open fire readiness report", "open iso 45001 audit pack",
        "inspect ready report", "ready to generate", "open competency report", "open risk register report"
    ],
    "SCHEDULE_REPORT": [
        "حفظ كتقرير مجدول", "جدولة التقرير", "جدولة إرسال التقرير", "جدولة الإرسال الآلي", "جدولة التقرير أسبوعيا",
        "جدولة التقرير شهريا", "حفظ التقرير المجدول", "تفعيل التقرير المجدول", "تفعيل الجدولة الآلية",
        "حفظ كتقرير مجدول شهرياً", "حفظ كتقرير مجدول اسبوعياً", "جدولة إرسال",
        "schedule report", "save scheduled report", "save as scheduled report", "automate report schedule",
        "schedule recurring report", "schedule report monthly"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 3: INCIDENTS, OBSERVATIONS & ROOT CAUSE ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    "CREATE_INCIDENT": [
        "create incident", "report incident", "log incident", "new accident", "near miss", "injury", "spill",
        "fire outbreak", "chemical release", "crush injury", "fall from height", "lost time incident", "lti",
        "first aid case", "restricted work case", "property damage", "report near miss",
        "بلاغ حادث", "تسجيل حادث", "اصابة عمل", "إصابة عمل", "حادث وشيك", "تسريب", "انسكاب", "حادث حريق",
        "حادث جديد", "ابلاغ عن حادث", "تسجيل اصابة", "حادث سقوط", "ماس كهربائي", "حادث سيرفر", "حالة اسعاف"
    ],
    "EXPORT_INCIDENTS_EXCEL": [
        "تصدير excel", "تصدير اكسل", "تصدير الإكسل", "تصدير ملف excel", "تصدير ملف اكسل",
        "تصدير الحوادث إلى excel", "تصدير الحوادث لاكسل", "تصدير الحوادث لاكسيل", "تصدير سجل الحوادث",
        "تصدير سجل الحوادث اكسل", "تصدير سجل الحوادث excel", "تحميل ملف excel للحوادث",
        "تحميل اكسل", "تنزيل اكسل", "تصدير السجل", "شيت اكسل الحوادث", "تقرير الحوادث excel",
        "تصدير الحوادث إلى ملف excel", "تصدير لملف إكسل", "استخراج اكسل", "تصدير جدول الحوادث",
        "تصدير كل الحوادث excel", "تحميل شيت الحوادث", "تصدير بيانات الحوادث",
        "export excel", "export to excel", "export incidents to excel", "export incidents excel",
        "download excel", "download incidents spreadsheet", "export incident register",
        "export to xlsx", "generate excel report", "dump incidents to excel", "download incident log excel"
    ],
    "GENERATE_REPORT_TEMPLATE": [
        "توليد نموذج مكتب العمل", "نموذج مكتب العمل", "إخطار إصابة عمل مكتب العمل", "إخطار مكتب العمل",
        "استمارة مكتب العمل", "نموذج إصابة مكتب العمل", "بلاغ مكتب العمل", "إخطار مكتب العمل بإصابة",
        "توليد نموذج مكتب العمل — إخطار إصابة", "توليد نموذج مكتب العمل لاخطار اصابة", "نموذج القوى العاملة",
        "توليد نموذج التأمينات", "توليد نموذج التأمينات الاجتماعية", "نموذج التأمينات الاجتماعية",
        "استمارة 1 إصابات", "استمارة 1 اصابات", "إخطار التأمينات الاجتماعية", "إخطار التأمينات",
        "استمارة إصابة التأمينات", "نموذج التأمين الاجتماعي", "توليد استمارة التأمينات",
        "توليد مطالبة التأمين", "مطالبة شركة التأمين", "مطالبة التأمين", "إخطار شركة التأمين للحادث",
        "مطالبة تأمين الحادث", "تقرير شركة التأمين", "مطالبة تعويض الحادث", "توليد مطالبة شركة التأمين",
        "توليد إخطار جهاز شؤون البيئة", "إخطار جهاز شؤون البيئة", "إخطار جهاز شئون البيئة",
        "إخطار البيئة", "إخطار شؤون البيئة", "بلاغ شؤون البيئة", "تقرير جهاز البيئة",
        "قوالب الإبلاغ الخارجي", "قوالب الابلاغ الخارجي", "توليد قوالب الإبلاغ الخارجي", "النماذج الخارجية",
        "labor office form", "labor office injury notice", "generate labor office report",
        "social insurance form", "social insurance injury notice", "generate insurance claim",
        "environmental agency notification", "statutory external templates"
    ],
    "MANAGE_RCA": [
        "تحليل السبب الجذري", "سجل تحليل السبب الجذري", "تحليل rca", "إضافة تحليل السبب الجذري",
        "توثيق rca", "تسجيل تحليل rca", "سجل rca", "السبب الجذري للحادث", "توثيق السبب الجذري",
        "تحليل السبب الجذري للحادث", "5 whys", "5-whys", "طريقة 5 لماذا", "fishbone", "عظم السمكة",
        "إيشيكاوا", "ishikawa", "root cause analysis", "create rca", "record root cause"
    ],
    "GET_ROOT_CAUSES": [
        "تحليل الأسباب الجذرية — ytd", "تحليل الأسباب الجذرية ytd", "تحليل الاسباب الجذرية ytd",
        "الأسباب الجذرية الأكثر تكراراً", "الاسباب الجذرية الاكثر تكرارا", "نسب أسباب الحوادث",
        "إحصائيات أسباب الحوادث", "ملخص الأسباب الجذرية", "root causes ytd", "root cause breakdown",
        "top root causes", "ytd root cause analysis"
    ],
    "LOG_SAFETY_OBSERVATION": [
        "log observation", "unsafe act", "unsafe condition", "positive safety observation", "observation",
        "safety hazard report", "behavioral observation", "safety flash", "log safety observation",
        "تسجيل سلوك غير آمن", "سلوك غير آمن", "حالة غير آمنة", "ملاحظة سلامة", "تسجيل ملاحظة", "تصرف خطر", "ملاحظة",
        "رصد تصرف غير آمن", "ظرف غير آمن", "ملاحظة إيجابية", "تقرير عين السلامة", "سلوك غير امن", "تصرف غير امن"
    ],
    "LIST_INCIDENTS": [
        "list incidents", "show accidents", "active incidents", "recent incidents", "incidents list",
        "open investigations", "incident log", "spill log", "accident history",
        "الحوادث المفتوحة", "البلاغات المفتوحة", "اعرض الحوادث المفتوحة", "فلترة الحوادث على المفتوح",
        "الحوادث المغلقة", "البلاغات المغلقة", "اعرض الحوادث المغلقة", "الحوادث تحت التحقيق",
        "قائمة الحوادث", "سجل البلاغات", "عرض الحوادث", "الحوادث المفتوحة", "احصائيات الحوادث", "سجل الحوادث",
        "الحوادث المسجلة", "سجل الإصابات", "بلاغات الحوادث", "جميع الحوادث"
    ],
    "GET_INCIDENT_DETAILS": [
        "incident details", "incident investigation", "root cause", "rca", "investigate", "5 whys", "fishbone analysis",
        "witness statement", "investigation report", "root cause of", "root cause for",
        "تفاصيل الحادث", "تحقيق الحادث", "السبب الجذري", "تقرير الحادث", "تحقيق", "تحليل السبب الجذري",
        "طريقة 5 لماذا", "مخطط عظم السمكة", "إفادة الشهود", "نتائج التحقيق", "السبب الجذري للحادث"
    ],
    "UPDATE_INCIDENT": [
        "update incident", "close incident", "investigate incident", "change incident status", "finalize investigation",
        "تحديث الحادث", "اغلاق البلاغ", "إغلاق البلاغ", "تعديل حالة الحادث", "انهاء التحقيق", "إغلاق ملف الحادث", "تعديل بيانات الحادث"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 4: ELECTRONIC PERMIT TO WORK (EPTW) & SIMOPS
    # ══════════════════════════════════════════════════════════════════════════
    "CREATE_PERMIT": [
        "create permit", "create a permit", "create work permit", "create a work permit", "issue permit", "issue a permit",
        "issue work permit", "issue a work permit", "new ptw", "request permit", "request a permit", "new work permit",
        "hot work permit", "confined space permit", "work at height permit", "electrical permit", "loto permit",
        "excavation permit", "radiography permit", "carrying shipments", "carrying shipment", "permit for", "lifting permit",
        "request a hot work permit", "request hot work permit", "request a work permit",
        "اصدار تصريح", "طلب تصريح عمل", "تصريح عمل ساخن", "تصريح دخول اماكن مغلقة", "تصريح مرتفعات", "تصريح كهربائي",
        "تصريح حفر", "تصريح لوتو", "تصريح عزل", "انشاء تصريح", "انشئ تصريح", "تصريح جديد", "اصدار تصريح عمل", "إصدار تصريح",
        "طلب تصريح", "تصريح ساخن", "تصريح لحام", "عمل ساخن", "اماكن مغلقة", "تصريح عمل", "اصدر تصريح", "إصدر تصريح",
        "نقل شحنات", "تصريح نقل", "تصريح شحنات", "تصريح شحن", "تصريح عمل لنقل", "عمل تصريح", "سوي تصريح", "اعمل تصريح",
        "تصريح رفع احمال", "تصريح اوناش", "تصريح اعمال باردة"
    ],
    "APPROVE_PERMIT": [
        "approve permit", "sign permit", "validate permit", "authorize ptw", "activate permit", "approve and activate permit",
        "approve and activate", "accept permit", "sign off permit", "authorize permit", "approve ptw", "activate ptw",
        "اعتماد وتفعيل التصريح", "اعتماد وتفعيل", "اعتماد وتفعيل تصريح", "تفعيل التصريح", "تفعيل تصريح", "تفعيل تصريح العمل",
        "اعتمد وفعل", "اعتمد وفعل تصريح", "اعتمد وتفعيل", "فعل تصريح", "فعل التصريح",
        "اعتماد تصريح", "الموافقة على التصريح", "توقيع التصريح", "اعتماد تصريح العمل", "تصريح معتمد",
        "الموافقة على ptw", "اعتمد تصريح", "اعتمد التصريح", "الموافقة على تصريح العمل", "اعتمد", "اعتماد", "اعتماد التصريح رقم", "اعتمد التصريح رقم"
    ],
    "SUSPEND_PERMIT": [
        "suspend permit", "freeze permit", "halt permit", "stop permit", "pause ptw", "abort permit",
        "تعليق تصريح", "إيقاف تصريح", "ايقاف تصريح", "وقف تصريح", "تجميد تصريح", "وقف العمل بالتصريح",
        "اوقف تصريح", "أوقف تصريح", "اوقف التصريح", "أوقف التصريح", "علق تصريح", "تجميد تصريح العمل"
    ],
    "CLOSE_PERMIT": [
        "close permit", "complete permit", "finish permit", "terminate ptw", "sign off permit",
        "handover site", "site reinstatement", "close work permit",
        "اغلاق تصريح", "إغلاق تصريح", "انهاء تصريح", "إنهاء تصريح", "تسليم تصريح", "اغلاق تصريح العمل", "إغلاق تصريح العمل",
        "انهاء تصريح العمل", "اغلق تصريح", "أغلق تصريح", "اغلق التصريح", "أغلق التصريح", "اقفل تصريح", "انهي تصريح", "أنهي تصريح",
        "إغلاق وتسليم الموقع", "اغلاق وتسليم الموقع", "تسليم الموقع", "إنهاء العمل وتسليم الموقع"
    ],
    "CLOSE_ALL_PERMITS": [
        "close all permits", "close all", "close all active permits", "terminate all permits", "shut down permits", "emergency site shutdown",
        "close all permits and handover", "close all active work permits",
        "اغلق كافة التصاريح", "إغلاق كافة التصاريح", "اغلق جميع التصاريح", "إغلاق جميع التصاريح", "إغلاق كل التصاريح", "اغلق كل التصاريح",
        "إغلاق كافة تصاريح العمل", "اغلاق كافة تصاريح العمل", "اغلاق كل تصاريح العمل", "إنهاء جميع التصاريح", "انهاء جميع التصاريح",
        "اغلق كافة تصاريح العمل النشطة", "إغلاق كافة تصاريح العمل النشطة", "اغلق جميع تصاريح العمل النشطة",
        "اغلق كافة تصاريح العمل النشطة وتسليم الموقع", "إغلاق كافة تصاريح العمل النشطة وتسليم الموقع",
        "اغلاق كافة تصاريح العمل وتسليم الموقع", "اغلاق وتسليم الموقع"
    ],
    "LIST_PERMITS": [
        "list permits", "active permits", "show ptw", "open work permits", "permits list", "all permits", "expired permits", "suspended permits", "expiring permits",
        "قائمة التصاريح", "سجل التصاريح", "عرض تصاريح العمل", "سجل تصاريح", "تصاريح العمل", "تصاريح منتهية", "تصاريح موقوفة", "تصاريح تنتهي قريبا", "تصاريح"
    ],
    "GET_PERMIT_DETAILS": [
        "permit details", "ptw gas test", "permit approvals", "ptw checklist", "view permit", "inspect permit",
        "تفاصيل التصريح", "فحص غازات التصريح", "موافقات التصريح", "قائمة فحص التصريح", "بيانات التصريح", "معلومات التصريح", "فحص تصريح"
    ],
    "UPDATE_PERMIT": [
        "update permit", "modify permit", "extend permit", "renew permit", "change permit", "edit permit",
        "change the location", "change location", "change zone", "change the zone", "change area", "move permit",
        "update location", "update zone", "set location", "set zone", "change description", "update description",
        "change contractor", "update contractor", "change executor", "update executor", "change risk", "update risk",
        "extend duration", "extend validity", "add hours", "extend ptw", "update ptw", "modify ptw", "change ptw", "edit ptw",
        "production line c", "line c", "zone c", "area c",
        "تعديل تصريح", "تحديث تصريح", "تمديد تصريح", "مد فترة التصريح", "تعديل تصريح العمل", "تمديد تصريح العمل", "تعديل ptw", "تحديث ptw",
        "تغيير موقع التصريح", "تغيير موقع تصريح", "تغيير مكان التصريح", "تغيير مكان تصريح", "تغيير عنبر التصريح", "تغيير منطقة التصريح",
        "نقل التصريح إلى", "نقل تصريح العمل إلى", "تعديل موقع التصريح", "تعديل مكان التصريح", "تعديل عنبر التصريح", "تحديث موقع التصريح",
        "خط الإنتاج c", "خط الانتاج c", "عنبر c", "منطقة c", "خط c",
        "تعديل وصف التصريح", "تغيير وصف التصريح", "تحديث وصف التصريح", "تعديل الاعمال في التصريح", "تغيير اعمال التصريح",
        "تغيير المقاول في التصريح", "تعديل المنفذ في التصريح", "تحديث المقاول في التصريح", "تغيير اسم المنفذ",
        "تعديل درجة خطورة التصريح", "تغيير خطورة التصريح", "تمديد مدة التصريح", "زيادة ساعات التصريح", "مد تصريح العمل",
        "تعديل بيانات التصريح", "تحديث بيانات التصريح", "تعديل التصريح رقم", "تحديث التصريح رقم"
    ],
    "DELETE_PERMIT": [
        "delete permit", "delete work permit", "delete ptw", "remove permit", "remove work permit", "remove ptw",
        "cancel permit", "cancel work permit", "cancel ptw", "purge permit", "remove ptw", "drop permit",
        "delete ptw-", "remove ptw-", "cancel ptw-", "purge ptw-",
        "cancelled by contractor", "cancelled by contrator", "cancellation by contractor", "cancelled by user",
        "حذف تصريح", "الغاء تصريح", "إلغاء تصريح", "شطب تصريح", "حذف تصريح العمل", "الغاء تصريح العمل", "إلغاء تصريح العمل",
        "احذف تصريح", "إحذف تصريح", "احذف التصريح", "إحذف التصريح", "الغاء ptw", "حذف ptw", "احذف ptw", "إحذف ptw",
        "امسح تصريح", "إمسح تصريح", "امسح التصريح", "إمسح التصريح", "مسح تصريح", "مسح التصريح", "شطب التصريح",
        "حذف تصريح رقم", "احذف تصريح رقم", "إلغاء تصريح رقم", "امسح تصريح رقم"
    ],
    "CHECK_SIMOPS": [
        "simops", "simultaneous operations", "permit conflicts", "overlapping permits", "conflict", "conflicts", "simops hazard",
        "تعارض التصاريح", "العمليات المتزامنة", "تعارض الاعمال", "تضارب تصاريح", "تعارض", "تعارض بين تصاريح", "تضارب", "تضارب اعمال", "سيموبس", "مخاطر العمليات المتزامنة"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 5: INSPECTIONS & AUDITS
    # ══════════════════════════════════════════════════════════════════════════
    "SCHEDULE_INSPECTION": [
        "schedule inspection", "routine safety walk", "book safety audit", "schedule walk", "new inspection", "plan inspection",
        "schedule safety walk", "weekly walk", "monthly inspection", "schedule weekly walk", "book walk", "schedule a new safety inspection",
        "جدولة", "بجدولة", "قم بجدولة", "جدول", "جدولة جولة", "بجدولة جولة", "جدول جولة", "جدولة جولة تفتيش", "بجدولة جولة تفتيش",
        "جدولة جولة تفتيش جديدة", "جدولة تفتيش", "بجدولة تفتيش", "جدولة فحص", "بجدولة فحص", "تفتيش دوري", "معاينة ميدانية",
        "جدولة جولة سلامة", "تفتيش جديد", "جدول تفتيش", "موعد تفتيش", "حجز موعد فحص", "تفتيش اسبوعي", "تفتيش أسبوعي", "حجز جولة"
    ],
    "SUBMIT_INSPECTION_WALK": [
        "submit inspection walk", "record walk", "completed inspection", "submit walk", "finish walkthrough", "start inspection walk",
        "start inspection", "start walk", "conduct walk", "certify walk", "complete safety walk",
        "بدء جولة تفتيش", "بدء جولة", "ابدأ جولة", "ابدأ جولة تفتيش", "تسجيل جولة تفتيش", "اعتماد جولة ميدانية", "توثيق جولة تفتيش",
        "إنهاء تفتيش", "تسجيل جولة ميدانية", "اعتماد التفتيش", "تنفيذ جولة تفتيش", "توثيق تفتيش"
    ],
    "LIST_INSPECTIONS": [
        "list inspections", "inspection history", "audit results", "safety walks", "inspections list", "inspections",
        "قائمة التفتيش", "سجل الجولات", "نتائج التفتيش", "سجل المعاينات", "جولات السلامة", "جولات التفتيش", "ملاحظات الفحص",
        "الفحص المفتوحة", "جولات", "جدول الجولات"
    ],
    "GET_INSPECTION_DETAILS": [
        "inspection details", "view inspection", "check inspection", "inspect details",
        "تفاصيل التفتيش", "بيانات جولة الفحص", "تقرير التفتيش", "عرض التفتيش", "تفاصيل الجولة"
    ],
    "GET_INSPECTION_STATS": [
        "inspection stats", "inspection compliance", "walk statistics", "inspection summary", "ai inspection assistant",
        "احصائيات التفتيش", "نسبة التزام التفتيش", "مؤشرات جولات السلامة", "احصائيات الجولات", "معدل الامتثال للتفتيش", "مساعد التفتيش الذكي ai", "مساعد التفتيش الذكي", "مساعد التفتيش"
    ],
    "CREATE_INSPECTION_FINDING": [
        "log finding", "inspection finding", "non-conformance", "audit finding", "finding", "new finding", "add finding", "create finding",
        "تسجيل ملاحظة تفتيش", "ملاحظة عدم مطابقة", "تسجيل مخالفة", "مخالفة تفتيش", "ملاحظة تفتيش", "رصد عدم مطابقة", "مخالفة سلامة", "اضافة ملاحظة تفتيش", "تسجيل ملاحظة"
    ],
    "UPDATE_INSPECTION": [
        "complete inspection", "update inspection", "submit inspection score", "modify inspection",
        "انهاء التفتيش", "تحديث نتيجة الفحص", "تسجيل درجة التفتيش", "إغلاق التفتيش", "تعديل التفتيش"
    ],
    "UPDATE_INSPECTION_FINDING": [
        "update finding", "close finding", "resolve finding", "fix finding", "update non-conformance", "close inspection finding",
        "ملاحظات عدم المطابقة", "ملاحظات السلامة", "اغلاق ملاحظة", "إغلاق ملاحظة", "إغلاق ملاحظة التفتيش", "تحديث الملاحظة", "حل الملاحظة", "معالجة المخالفة", "اغلاق مخالفة", "إغلاق مخالفة"
    ],
    "DELETE_INSPECTION": [
        "delete inspection", "remove inspection", "cancel inspection walk", "drop inspection",
        "حذف تفتيش", "احذف جولة التفتيش", "الغاء جولة التفتيش", "مسح التفتيش", "شطب التفتيش"
    ],
    "DELETE_INSPECTION_FINDING": [
        "delete finding", "remove finding", "delete non-conformance",
        "حذف ملاحظة", "احذف ملاحظة التفتيش", "مسح الملاحظة", "شطب المخالفة"
    ],
    "GENERATE_INSPECTION_CHECKLIST": [
        "generate inspection checklist", "inspection checklist for", "checklist advisor", "inspection standard items", "inspection form builder",
        "بانى نماذج التفتيش", "باني نماذج التفتيش", "قائمة فحص تفتيش", "بنود التفتيش", "قائمة تدقيق السلامة", "اقتراح قائمة فحص", "بنود فحص", "نماذج التفتيش"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 6: CAPA (CORRECTIVE & PREVENTIVE ACTIONS)
    # ══════════════════════════════════════════════════════════════════════════
    "CREATE_CAPA": [
        "create capa", "new corrective action", "log preventive action", "add capa", "remediation plan", "create a new corrective action",
        "اجراء تصحيحي", "إجراء تصحيحي", "اجراء وقائي", "إجراء وقائي", "تسجيل خطة عمل", "انشاء capa", "انشئ capa", "خطة تصحيح"
    ],
    "LIST_CAPAS": [
        "list capas", "overdue capas", "open corrective actions", "all capas", "capas list", "capa", "capas",
        "الاجراءات التصحيحية المتأخرة", "قائمة capa", "سجل الاجراءات الوقائية", "خطط العمل", "الاجراءات التصحيحية", "إجراءات capa", "اجراءات capa", "كابا", "المتأخرة", "متأخرة", "قائمة الإجراءات التصحيحية"
    ],
    "UPDATE_CAPA": [
        "update capa", "complete capa", "close corrective action", "verify capa", "action item closed",
        "تحديث الاجراء", "إغلاق الإجراء التصحيحي", "انهاء خطة العمل", "اعتماد الاجراء", "اغلاق capa", "التحقق من تنفيذ الإجراء"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 7: RISK REGISTER & HIRA
    # ══════════════════════════════════════════════════════════════════════════
    "CREATE_RISK": [
        "create risk", "risk assessment", "hazard identification", "hazard matrix", "new hazard", "hira assessment",
        "hazard identification and risk assessment", "add risk", "create risk assessment", "hazard identification and risk assessment for",
        "تقييم مخاطر", "تحليل سلامة العمل", "تسجيل خطر", "خطر جديد", "اضافة خطر", "تحديد المخاطر", "تقييم مخاطر جديد", "انشاء تقييم خطر"
    ],
    "LIST_RISK": [
        "list risks", "show risk register", "risk matrix", "high risks", "risks list", "hazards", "extreme risks", "risk register", "all hazards",
        "قائمة المخاطر", "سجل تقييم المخاطر", "سجل المخاطر العام", "سجل المخاطر", "مصفوفة المخاطر", "مصفوفة الخطر", "المخاطر العالية", "سجل الخطر", "المخاطر الحرجة", "عرض المخاطر", "سجل hira", "سجل مخاطر"
    ],
    "GET_HIGH_RISK_HAZARDS": [
        "high risk hazards", "critical risks", "top risks", "most dangerous hazards", "severe risks",
        "أخطر المخاطر", "المخاطر الشديدة", "المخاطر الحرجة", "اعلى المخاطر", "أعلى المخاطر المسجلة"
    ],
    "CALCULATE_RESIDUAL_RISK": [
        "calculate residual risk", "risk reduction", "hierarchy of controls calculation",
        "حساب الخطر المتبقي", "نسبة تقليل الخطر", "حساب اثر التحكم"
    ],
    "GET_RISK_DETAILS": [
        "risk details", "hazard profile", "risk assessment details",
        "تفاصيل الخطر", "بيانات تقييم الخطر", "معلومات الخطر"
    ],
    "UPDATE_RISK": [
        "update risk", "modify risk controls", "residual risk", "re-assess hazard",
        "تحديث تقييم المخاطر", "تعديل التحكم", "الخطر المتبقي", "إعادة تقييم الخطر"
    ],
    "DELETE_RISK": [
        "delete risk", "remove hazard", "purge risk",
        "حذف خطر", "مسح الخطر من السجل", "إلغاء الخطر"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 8: JOB SAFETY ANALYSIS (JSA / JHA)
    # ══════════════════════════════════════════════════════════════════════════
    "CREATE_JSA": [
        "create jsa", "new jsa", "job safety analysis", "task risk breakdown", "swms creation", "safe work method statement",
        "job safety analysis for",
        "سلامة مهام", "سلامة المهام", "تحليل مهام", "انشاء jsa", "انشئ jsa",
        "تحليل سلامة المهام", "تحليل مخاطر العمل", "انشاء تحليل مهام", "انشئ تحليل", "بيان طريقة العمل الآمنة"
    ],
    "LIST_JSAS": [
        "list jsa", "show jsas", "jsa catalog", "task analysis", "jsas list", "approved jsas", "jsa list", "list jsas", "all jsas",
        "قائمة jsa", "سجل تحليل المهام", "نماذج jsa", "تحليلات السلامة", "سجل jsa", "وثائق تحليل سلامة المهام", "قائمة نماذج تحليل سلامة المهام", "قائمة نماذج jsa", "تحاليل سلامة المهام", "تحاليل المهام"
    ],
    "GET_JSA_DETAILS": [
        "jsa details", "jsa steps", "task steps breakdown", "jsa hazard steps",
        "تفاصيل jsa", "خطوات المهمة", "خطوات تحليل سلامة المهام", "بيانات jsa"
    ],
    "MANAGE_JSA_STEPS": [
        "add jsa step", "update jsa step", "delete jsa step", "jsa steps",
        "اضافة خطوة jsa", "تعديل خطوة في jsa", "حذف خطوة من jsa"
    ],
    "LINK_JSA_PERMIT": [
        "link jsa permit", "link permit to jsa", "unlink jsa permit",
        "ربط jsa بتصريح", "ربط تصريح العمل بـ jsa", "فك ربط jsa"
    ],
    "UPDATE_JSA": [
        "update jsa", "approve jsa", "modify task controls", "revise jsa",
        "تحديث jsa", "اعتماد تحليل المهام", "تعديل اجراءات jsa", "اعتماد jsa", "مراجعة تحليل المهام"
    ],
    "DELETE_JSA": [
        "delete jsa", "remove jsa", "purge jsa",
        "حذف jsa", "مسح تحليل سلامة المهام"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 9: TRAINING, CERTIFICATIONS & COMPETENCY
    # ══════════════════════════════════════════════════════════════════════════
    "RENEW_CERTIFICATE": [
        "renew", "renewal", "re-certify", "recertify", "extend certificate", "refresh cert", "extend validity",
        "renew certificate", "renew cert", "renew license",
        "تجديد", "جدد", "جددها", "تمديد الشهادة", "تجديد شهادة", "مد صلاحية", "اعادة اصدار", "إعادة إصدار", "تجديد رخصة", "تجديد شهادة السلامة", "مد صلاحية الشهادة"
    ],
    "CREATE_CERTIFICATE": [
        "create certificate", "issue certificate", "new certificate", "add training", "grant license", "register certificate",
        "اصدار شهادة", "إصدار شهادة", "تسجيل دورة", "اضافة شهادة", "منح شهادة", "شهادة جديدة", "توثيق تدريب"
    ],
    "LIST_CERTIFICATES": [
        "list certificates", "show certificates", "training schedule", "matrix", "overdue training", "certificates list",
        "competency matrix", "expired licenses", "expired certificates",
        "سجل الشهادات", "قائمة الشهادات", "جدول التدريبات", "مصفوفة الكفاءة", "عرض الشهادات", "تدريب منتهي", "شهادات", "الشهادات التدريبية", "رخص منتهية", "الشهادات التدريبية المنتهية الصلاحية", "الشهادات المنتهية"
    ],
    "CREATE_TRAINING_COURSE": [
        "create course", "add training course", "new course program", "course catalog", "safety training program",
        "اضافة دورة تدريبية", "إنشاء كورس تدريبي", "اضافة برنامج تدريب", "دورة جديدة", "كورس جديد", "برنامج تدريبي"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 10: PPE MANAGEMENT & INVENTORY
    # ══════════════════════════════════════════════════════════════════════════
    "CREATE_PPE_SUPPLY_ORDER": [
        "supply order", "reorder ppe", "ppe supply request", "procure ppe", "order ppe", "restock ppe", "reorder threshold",
        "low stock ppe", "purchase requisition",
        "طلب توريد", "طلب شراء", "توريد مهمات", "شراء مهمات", "إعادة طلب", "اعمل طلب توريد", "ارفع طلب توريد", "الأصناف الناقصة",
        "تحت حد الطلب", "طلب توريد تلقائي", "توريد مهمات الوقاية", "اصناف تحت حد الطلب", "طلب شراء مهمات", "طلب توريد مهمات", "مهمات الوقاية الناقصة"
    ],
    "ISSUE_PPE": [
        "issue ppe", "dispense ppe", "give safety helmet", "give one safety helmet", "giveaway", "give away", "give helmet", "give one",
        "assign gear", "ppe transaction", "return ppe", "log transaction", "dispense helmet", "issue helmet", "issue glasses",
        "issue gloves", "issue boots", "hand out ppe", "give ppe", "giveaway ppe", "dispense safety",
        "صرف مهمات", "صرف خوذة", "صرف حذاء", "صرف قفازات", "صرف نظارة", "تسليم وقاية", "تسجيل صرف", "تسجيل إرجاع", "تسجيل ارجاع",
        "إرجاع مهمة", "ارجاع مهمة", "إرجاع", "ارجاع", "حركة صرف", "حركة إرجاع", "حركة ارجاع", "صرف", "اصرف", "صرف 2 حذاء", "صرف حذاء أمان"
    ],
    "DELETE_PPE_TRANSACTION": [
        "delete ppe transaction", "cancel ppe transaction", "revert ppe transaction", "void transaction",
        "إلغاء حركة صرف", "الغاء حركة صرف", "حذف حركة صرف", "إلغاء حركة إرجاع", "الغاء حركة ارجاع", "حذف حركة مهمات", "تراجع عن الصرف"
    ],
    "ADD_PPE_ITEM": [
        "add ppe item", "new ppe gear", "register ppe", "create ppe item", "new safety product",
        "اضافة مهمة وقاية", "إضافة صنف وقاية", "أضف صنف وقاية", "اضف صنف وقاية", "إضافة صنف", "اضافة صنف", "أضف صنف", "اضف صنف",
        "تسجيل مهمة جديدة", "صنف مهمات جديد", "تسجيل صنف وقاية"
    ],
    "UPDATE_PPE_ITEM": [
        "update ppe item", "edit ppe item", "modify ppe", "update ppe details",
        "تعديل صنف وقاية", "تعديل بيانات الصنف", "تحديث صنف مهمة", "تعديل صنف", "تحديث صنف"
    ],
    "DELETE_PPE_ITEM": [
        "delete ppe item", "remove ppe item", "purge ppe item",
        "حذف صنف وقاية", "مسح صنف مهمة", "حذف صنف", "مسح صنف"
    ],
    "LIST_PPE": [
        "list ppe", "ppe inventory", "ppe stock", "ppe threshold", "ppe matrix", "ppe list", "ppe items", "protective gear catalog",
        "مخزون المهمات", "رصيد مهمات الوقاية", "مهمات اوشكت على النفاد", "مصفوفة المهمات", "مهمات الوقاية", "حالة مخزون مهمات الوقاية", "اصناف الوقاية", "أصناف الوقاية"
    ],
    "UPDATE_PPE_STOCK": [
        "update ppe stock", "restock ppe", "add ppe inventory", "set balance", "stock adjustment",
        "تحديث رصيد المهمات", "اضافة مخزون", "توريد مهمات وقاية", "تعديل رصيد مهمات", "تعديل رصيد", "تحديث الرصيد", "جرد المهمات"
    ],
    "DELETE_PPE_MATRIX_RULE": [
        "delete ppe matrix", "remove ppe matrix rule", "cancel mandatory ppe",
        "حذف من مصفوفة المهمات", "حذف قاعدة مصفوفة", "إلغاء إلزامية مهمة"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 11: FIRE SAFETY & FIXED EMERGENCY ASSETS
    # ══════════════════════════════════════════════════════════════════════════
    "LOG_FIRE_INSPECTION": [
        "log fire inspection", "inspect extinguisher", "check fire hose", "fire audit", "simulate scan", "qr scan", "mobile inspection",
        "scan qr", "qr code inspection", "qr-fe-a-014", "fe-a-014", "inspect fire equipment", "fire pressure test", "record inspection",
        "field inspection", "inspect unit", "fire inspection",
        "محاكاة مسح الكود", "مسح الكود", "مسح qr", "فحص qr", "محاكاة مسح qr", "فحص طفاية", "تفتيش الحريق", "فحص شبكة الاطفاء",
        "اختبار الضغط", "فحص دوري لطفايات", "فحص معدة الحريق", "فحص طفاية الحريق", "مسح كود المعدة", "تسجيل فحص لهذه المعدة",
        "تسجيل فحص ميداني", "سجل فحص", "فحص لهذه المعدة", "فحص ميداني", "تسجيل فحص دوري", "فحص الطفاية", "سجل فحص لمعدة الإطفاء",
        "فحص طفاية الحريق fe", "سجل فحص لطفاية"
    ],
    "SERVICE_FIRE_EQUIPMENT": [
        "service fire equipment", "refill extinguisher", "replace extinguisher", "fire work order", "recharge extinguisher",
        "extinguisher maintenance", "fire service order", "immediate replacement", "refill fire extinguisher",
        "صيانة معدة اطفاء", "صيانة طفاية", "استبدال فوري", "إعادة تعبئة", "اعادة تعبئة", "أمر شغل", "امر شغل", "عمرة طفاية",
        "تعبئة طفاية", "تغيير طفاية", "استبدال طفاية", "صيانة طفايات الحريق", "أمر صيانة", "أمر صيانة للمعدة", "إعادة تعبئة طفاية",
        "استبدال فوري لطفاية", "استبدال طفاية الحريق", "اعادة تعبئة طفاية الحريق", "صيانة معدات الإطفاء"
    ],
    "GET_FIRE_READINESS_REPORT": [
        "fire readiness report", "readiness report", "fire equipment report", "fire network readiness", "export readiness report",
        "fire compliance report", "sprinkler and hydrant status",
        "تقرير الجاهزية", "تقرير جاهزية معدات الحريق", "تقرير جاهزية شبكة الإطفاء", "تقرير الجاهزية لشبكة الإطفاء", "نسبة الجاهزية",
        "تصدير تقرير الجاهزية", "تقرير شبكة ومعدات الإطفاء", "جاهزية شبكة الإطفاء", "تقرير الحريق والجاهزية", "استخرج تقرير جاهزية"
    ],
    "GET_FIRE_INSPECTION_SCHEDULE": [
        "fire inspection schedule", "inspection schedule", "fire audit schedule", "next fire inspection", "periodic inspection schedule",
        "جدول الفحص", "جدول الفحص الدوري", "جدول فحص معدات الإطفاء", "جدول فحص طفايات الحريق", "مواعيد فحص معدات الإطفاء",
        "مواعيد فحص الحريق", "فحص الحريق القادم", "موعد الفحص الدوري", "جدول تفتيش الحريق", "متى موعد فحص الحريق"
    ],
    "GET_FIRE_EQUIPMENT_DETAIL": [
        "fire equipment details", "extinguisher details", "qr scan code", "equipment profile", "fire equipment qr",
        "تفاصيل معدة الإطفاء", "تفاصيل طفاية الحريق", "كود المسح الميداني", "كود qr لطفاية", "بيانات معدة الإطفاء",
        "بيانات الطفاية", "موقع الطفاية", "صلاحية معدة الإطفاء", "تفاصيل المعدة", "معلومات طفاية الحريق"
    ],
    "GET_FIRE_ATTENTION_LIST": [
        "fire attention list", "expired fire equipment", "fire equipment needing attention", "urgent fire repairs",
        "معدات تحتاج انتباه فوري", "طفايات تحتاج انتباه", "طفايات منتهية الصلاحية", "المعدات المعطلة", "طفايات معيبة",
        "معدات الحريق المنتهية", "معدات تحتاج صيانة", "معدات تحتاج استبدال", "انتباه فوري"
    ],
    "GET_FIRE_COVERAGE_BY_ZONE": [
        "fire coverage by zone", "fire network coverage", "extinguisher zone coverage", "zone readiness breakdown",
        "تغطية وجاهزية الشبكة حسب المنطقة", "تغطية شبكة الإطفاء", "تغطية معدات الحريق بالمناطق", "جاهزية المناطق الصناعية",
        "توزيع طفايات الحريق", "نسبة تغطية الحريق"
    ],
    "GET_FIRE_EQUIPMENT_STATS": [
        "fire equipment stats", "fire kpis", "smoke detectors count", "fire hydrants pressure", "serviceable extinguishers count",
        "إحصائيات معدات الحريق", "إحصائيات الإطفاء", "عدد كواشف الدخان", "ضغط حنفيات الحريق", "كم عدد معدات الإطفاء الجاهزة"
    ],
    "INSPECT_FIXED_SAFETY_ASSET": [
        "inspect eyewash", "test emergency shower", "inspect safety shower", "test aed", "inspect fixed safety asset", "fixed asset inspection",
        "check spill kit", "test fire alarm panel", "inspect emergency eyewash", "test emergency eyewash",
        "فحص محطة غسيل العيون", "اختبار محطة غسيل العيون", "غسيل العيون", "غسيل عيون", "دش الطوارئ", "دش طوارئ", "محطة غسيل",
        "فحص دش الطوارئ", "اختبار دش الطوارئ", "فحص أجهزة الصدمات", "فحص اجهزة الصدمات", "أجهزة الصدمات", "اجهزة الصدمات",
        "فحص معدات السلامة الثابتة", "اختبار معدات السلامة الثابتة", "فحص صندوق الإسعاف", "فحص حقيبة الانسكاب", "فحص واختبار محطة غسيل العيون"
    ],
    "ADD_FIRE_EQUIPMENT": [
        "add fire extinguisher", "new fire equipment", "install extinguisher", "fixed asset", "add fixed safety asset",
        "اضافة طفاية", "إضافة طفاية حريق", "تركيب خرطوم اطفاء", "محطة غسيل عيون", "اضافة اصل سلامة", "طفاية جديدة",
        "إضافة معدة سلامة ثابتة", "اضافة معدة سلامة ثابتة", "تركيب طفاية جديدة", "إضافة معدة", "اضافة معدة", "تسجيل طفاية جديدة",
        "إضافة طفاية جديدة في zone"
    ],
    "LIST_FIRE_EQUIPMENT": [
        "list fire equipment", "expired extinguishers", "fire assets", "eyewash stations", "fire equipment", "fire extinguishers",
        "fixed safety assets", "fire suppression inventory", "hose reels catalog", "filter fire equipment",
        "معدات الحريق", "طفايات منتهية", "صمامات الحريق", "محطات غسيل العيون", "معدات السلامة الثابتة", "أجهزة الصدمات",
        "طفايات الحريق", "مطافئ الحريق", "معدات ومطافئ الحريق", "مطافئ", "طفايات", "شبكة إطفاء الحريق", "معدات ومطافئ الحريق المنتهية",
        "فلترة معدات الحريق", "معدات الإطفاء في zone"
    ],
    "DELETE_FIXED_SAFETY_ASSET": [
        "delete fixed safety asset", "remove fixed asset", "decommission asset",
        "حذف معدة سلامة ثابتة", "مسح محطة غسيل عيون", "حذف أصل سلامة", "إلغاء معدة إطفاء"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 12: HAZMAT & CHEMICALS
    # ══════════════════════════════════════════════════════════════════════════
    "ADD_CHEMICAL": [
        "add chemical", "register chemical", "new hazardous material", "cas number", "add sds sheet",
        "register new chemical", "new chemical", "add new chemical", "add hazardous material", "add hazardous materials",
        "add to hazardous materials", "add to hazmat", "add calcuim cianade to the hazardous materials",
        "add calcium cyanide", "add cyanide", "register hazardous chemical", "new hazmat chemical", "create chemical",
        "insert chemical", "store chemical in hazmat", "record chemical in hazmat inventory", "new chemical product",
        "add to chemical register", "add substance to hazmat", "store hazardous material",
        "اضافة مادة كيميائية", "إضافة مادة", "تسجيل مادة خطرة", "بيانات السلامة الكيميائية", "مادة كيميائية جديدة", "تسجيل خام كيميائي",
        "تسجيل مادة كيميائية جديدة", "اضافة مادة جديدة", "اضافة سيانيد الكالسيوم الى المواد الخطرة",
        "أضف سيانيد الكالسيوم إلى المواد الخطرة", "أضف إلى المواد الخطرة", "اضف للمواد الخطرة",
        "تسجيل مادة في المواد الخطرة", "حط في المواد الخطرة", "حط مادة خطرة", "إضافة مادة للمخزون الكيميائي",
        "سجل مادة خطرة جديدة", "إضافة مادة كيميائية جديدة", "اضافة سيانيد الكالسيوم", "أضف سيانيد الكالسيوم",
        "سجل سيانيد الكالسيوم", "تسجيل سيانيد الكالسيوم", "حطلي سيانيد الكالسيوم", "حط سيانيد الكالسيوم"
    ],
    "LIST_CHEMICALS": [
        "list chemicals", "chemical inventory", "ghs classes", "hazmat", "hazardous materials", "hazmat materials",
        "hazmat inventory", "chemical compatibility", "chemicals", "sds library", "all chemicals",
        "show hazardous materials", "list hazardous chemicals", "chemical stock", "hazmat register",
        "قائمة المواد الكيميائية", "المواد الخطرة", "المواد الخطره", "المواد الخطرة والكيماويات", "سجل المواد الخطرة",
        "سجل الكيماويات والمخزون", "مخزون المواد الخطرة", "توافق المواد الكيميائية", "تصنيفات ghs", "المواد الكيميائية",
        "سجل الكيماويات", "المواد الكيميائية الخطرة", "المواد الكيميائية الخطرة المسجلة", "عرض المواد الخطرة",
        "استعراض الكيماويات", "استعراض المواد الخطرة", "قائمة المواد الخطرة"
    ],
    "GET_CHEMICAL_DETAILS": [
        "chemical details", "sds sheet", "ghs hazards", "chemical profile", "cas number lookup",
        "hazardous material profile", "substance info", "calcium cyanide details", "chemical card",
        "تفاصيل المادة الكيميائية", "بيانات المادة", "بطاقة السلامة الكيميائية", "معلومات المادة الكيميائية",
        "كارت المادة الخطرة", "تفاصيل سيانيد الكالسيوم", "معلومات سيانيد الكالسيوم", "بيانات سيانيد الكالسيوم",
        "بطاقة مادة خطرة", "تفاصيل المادة"
    ],
    "CHECK_CHEMICAL_STORAGE": [
        "check chemical storage", "chemical storage safety", "nfpa 400 audit", "segregation safety", "storage compliance",
        "chemical compatibility audit", "hazmat segregation", "storage safety check",
        "سلامة تخزين الكيماويات", "فحص مستودع الكيماويات", "توافق التخزين الكيميائي", "مطابقة تخزين المواد الخطرة",
        "توافق المواد الخطرة", "فصل المواد الكيميائية", "فحص أمان تخزين المواد الخطرة", "أمان تخزين الكيماويات"
    ],
    "UPDATE_CHEMICAL": [
        "update chemical", "update chemical stock", "change chemical quantity", "modify chemical", "adjust hazmat stock", "update hazmat record",
        "تعديل مادة كيميائية", "تحديث مخزون الكيماويات", "تعديل كمية مادة", "تحديث رصيد المادة", "تعديل بيانات مادة خطرة", "تحديث كمية مادة"
    ],
    "GET_MSDS": [
        "msds", "sds", "safety data sheet", "msds sheet", "chemical sds", "msds report", "sds document",
        "صحيفة بيانات السلامة", "نشرة السلامة", "ملف msds", "ورقة msds", "بيانات msds", "صحيفة sds", "وثيقة sds"
    ],
    "EMERGENCY_GUIDE": [
        "chemical emergency guide", "spill response guide", "first aid chemical", "emergency response hazmat", "chemical spill kit",
        "دليل طوارئ المواد الخطرة", "مكافحة انسكاب المواد", "إسعافات أولية للمواد الكيميائية", "طوارئ الكيماويات", "إرشادات الانسكاب الكيميائي"
    ],
    "SDS_ARCHIVE": [
        "sds archive", "sds records", "sds library", "safety data sheet archive", "expired sds", "current sds",
        "أرشيف صحائف السلامة", "ارشيف صحائف السلامة", "سجل sds", "أرشيف sds", "ارشيف sds", "صحائف السلامة المعتمدة"
    ],
    "DELETE_CHEMICAL": [
        "delete chemical", "remove chemical", "purge hazmat", "delete hazardous material", "remove from hazmat register",
        "حذف مادة كيميائية", "مسح المادة من السجل", "حذف مادة خطرة", "إلغاء مادة من المواد الخطرة", "حذف من المواد الخطرة"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 13: OCCUPATIONAL HEALTH & MEDICAL
    # ══════════════════════════════════════════════════════════════════════════
    "RECORD_MEDICAL_EXAM": [
        "record medical exam", "schedule medical exam", "fitness for duty", "audiometry", "spirometry", "medical exam",
        "medical record", "health record", "health exam", "create medical", "hearing", "hearing check", "hearing test",
        "hearing exam", "record exam", "schedule exam", "create exam", "register exam", "lung function test",
        "record periodic medical exam",
        "فحص طبي", "كشف طبي", "جدولة كشف دوري", "فحص السمع", "كفاءة طبية", "صلاحية طبية للعمل", "فحص طبي جديد",
        "سجل طبي", "سجل صحي", "فحص سمع", "كشف سمع", "تسجيل فحص", "إنشاء سجل طبي", "كشف اللياقة الطبية"
    ],
    "LIST_MEDICAL_EXAMS": [
        "list medical exams", "occupational exposure", "noise levels", "dust monitoring", "wearables", "health exams",
        "audiometry tests", "heat stress monitoring",
        "الفحوصات الطبية", "الصحة المهنية", "قياسات الضوضاء", "التعرض المهني", "الاجهزة الذكية", "سجل الفحوصات الطبية", "الفحوصات الطبية الدورية", "الفحوصات الطبية الدورية وقياسات السمع"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 14: AI VISION & IOT TELEMETRY
    # ══════════════════════════════════════════════════════════════════════════
    "ADD_IOT_SENSOR": [
        "add iot sensor", "register sensor", "install sensor", "voc sensor", "new sensor", "gas detector installation",
        "install new voc gas sensor", "install new sensor", "new voc gas sensor", "gas sensor",
        "اضافة حساس", "إضافة مستشعر", "أضف مستشعر", "اضف مستشعر", "أضف حساس", "اضف حساس", "حساس جديد", "تركيب كاشف غاز", "تركيب حساس جديد"
    ],
    "LIST_AI_IOT": [
        "iot sensors", "sensor alerts", "ai cameras", "ai events", "vision detections", "ppe violation", "sensors", "iot",
        "toxic gas alarm", "man down alert",
        "حساسات iot", "قراءات الحساسات", "كاميرات الذكاء الاصطناعي", "مخالفات الكاميرا", "كشف عدم ارتداء الخوذة",
        "انذارات الحساسات", "مستشعرات الغازات", "مستشعرات", "تنبيهات الكاميرات", "كشف السقوط"
    ],

    # ══════════════════════════════════════════════════════════════════════════
    # MODULE 15: GOVERNANCE, RAG STANDARDS & SECURITY
    # ══════════════════════════════════════════════════════════════════════════
    "LIST_SECURITY_ROLES": [
        "security roles", "rbac matrix", "user permissions", "system access", "rbac",
        "ادوار المستخدمين", "صلاحيات النظام", "مصفوفة الصلاحيات", "مستويات الوصول", "صلاحيات rbac"
    ],
    "MANAGE_USERS": [
        "list users", "user accounts", "user details", "assign role", "user profile", "active users",
        "المستخدمين", "قائمة المستخدمين", "حسابات المستخدمين", "بيانات المستخدم", "تعيين صلاحية", "ملف المستخدم"
    ],
    "MANAGE_INTEGRATIONS": [
        "integrations", "integration status", "sync integration", "erp sync", "sap connector", "external systems", "integration connectors", "outbox sync",
        "التكاملات", "الربط والتكامل", "أنظمة الربط", "حالة الربط", "مزامنة الربط", "ربط sap", "تكامل erp", "أنظمة التكامل الخارجية", "سجلات المزامنة"
    ],
    "GET_SYSTEM_ARCHITECTURE": [
        "system architecture", "system topology", "services status", "database metrics", "api catalog", "microservices", "tech stack", "architecture",
        "معمارية النظام", "هيكلية النظام", "الخدمات المشغلة", "مخطط النظام", "معمارية المنظومة", "الخدمات والمنافذ", "فهرس api", "حالة السيرفرات"
    ],
    "GET_SERVICE_HEALTH": [
        "service health", "health check", "system health", "database health", "server status",
        "صحة الخدمات", "فحص النظام", "حالة السيرفر", "سلامة النظام", "كفاءة المنظومة"
    ],
    "GET_TRIR_METRICS": [
        "trir", "ltifr", "total recordable incident rate", "lost time injury rate", "osha metrics", "incident rate",
        "معدل trir", "معدل ltifr", "معدل تكرار الإصابات", "معدل الحوادث القاتلة", "مؤشر trir", "مؤشر ltifr", "حساب معدل الاصابات"
    ],
    "VERIFY_AUDIT_LOG": [
        "verify audit log", "audit chain integrity", "tamper evident", "audit hash chain", "verify logs",
        "التحقق من سجل التدقيق", "صحة audit log", "نزاهة السجل المشفر", "التحقق من سجل التعديلات"
    ],
    "GET_SECURITY_AUDIT_SUMMARY": [
        "security audit summary", "security health", "mfa adoption", "security overview",
        "ملخص أمان النظام", "ملخص الأمان", "تقرير أمان المستخدمين", "احصائيات الامان"
    ],
    "SEARCH_RAG_KNOWLEDGE": [
        "osha standard", "osha", "iso 45001", "iso", "golden rules", "gas limits", "pel", "lel", "confined space rules",
        "egyptian labor law", "civil defense law", "stop work authority", "nfpa code",
        "معايير السلامة", "مواصفات osha", "ايزو 45001", "القواعد الذهبية", "حدود الغازات", "تعليمات السلامة",
        "اشتراطات", "شروط", "معايير", "مواصفات", "قواعد السلامة", "حدود التعرض", "قانون العمل المصري"
    ],
}


# ==============================================================================
# 3. INTENT TO MODULE & TOOL ROUTING MAPPINGS
# ==============================================================================

INTENT_TO_MODULE_MAP: Dict[str, int] = {
    # Module 1: Master Data
    "LIST_DEPARTMENTS": 1, "GET_DEPARTMENT_DETAILS": 1, "CREATE_DEPARTMENT": 1, "UPDATE_DEPARTMENT": 1, "DELETE_DEPARTMENT": 1,
    "LIST_ZONES": 1, "GET_ZONE_DETAILS": 1, "CREATE_ZONE": 1, "UPDATE_ZONE": 1, "DELETE_ZONE": 1, "GET_DEPARTMENT_ZONES_SUMMARY": 1,
    "LIST_EMPLOYEES": 1, "CREATE_EMPLOYEE": 1, "UPDATE_EMPLOYEE": 1, "GET_EMPLOYEE_INFO": 1,

    # Module 2: Dashboard & KPIs
    "GET_DASHBOARD_SUMMARY": 2, "REFRESH_DASHBOARD": 2, "GET_MONTHLY_KPIS": 2, "GET_SAFETY_SCORES": 2, "GET_TRIR_METRICS": 2,
    "LIST_AUDIT_LOGS": 2, "VERIFY_AUDIT_LOG": 2, "GET_SECURITY_AUDIT_SUMMARY": 2,
    "EXPORT_REPORTS_EXCEL": 2, "EXPORT_REPORTS_PDF": 2, "SEND_REPORT_TO_MANAGEMENT": 2, "GENERATE_CUSTOM_REPORT": 2, "OPEN_READY_REPORT": 2, "SCHEDULE_REPORT": 2,

    # Module 3: Incidents
    "CREATE_INCIDENT": 3, "LOG_SAFETY_OBSERVATION": 3, "LIST_INCIDENTS": 3, "GET_INCIDENT_DETAILS": 3, "UPDATE_INCIDENT": 3,
    "EXPORT_INCIDENTS_EXCEL": 3, "GENERATE_REPORT_TEMPLATE": 3, "MANAGE_RCA": 3, "GET_ROOT_CAUSES": 3,

    # Module 4: Permits
    "CREATE_PERMIT": 4, "APPROVE_PERMIT": 4, "SUSPEND_PERMIT": 4, "CLOSE_PERMIT": 4, "CLOSE_ALL_PERMITS": 4,
    "LIST_PERMITS": 4, "GET_PERMIT_DETAILS": 4, "UPDATE_PERMIT": 4, "DELETE_PERMIT": 4, "CHECK_SIMOPS": 4,

    # Module 5: Inspections
    "SCHEDULE_INSPECTION": 5, "SUBMIT_INSPECTION_WALK": 5, "LIST_INSPECTIONS": 5, "GET_INSPECTION_DETAILS": 5,
    "GET_INSPECTION_STATS": 5, "CREATE_INSPECTION_FINDING": 5, "UPDATE_INSPECTION": 5, "UPDATE_INSPECTION_FINDING": 5,
    "DELETE_INSPECTION": 5, "DELETE_INSPECTION_FINDING": 5, "GENERATE_INSPECTION_CHECKLIST": 5,

    # Module 6: CAPA
    "CREATE_CAPA": 6, "LIST_CAPAS": 6, "UPDATE_CAPA": 6,

    # Module 7: Risk Register (HIRA)
    "CREATE_RISK": 7, "LIST_RISK": 7, "GET_RISK_DETAILS": 7, "UPDATE_RISK": 7, "DELETE_RISK": 7,
    "CALCULATE_RESIDUAL_RISK": 7, "GET_HIGH_RISK_HAZARDS": 7,

    # Module 8: JSA
    "CREATE_JSA": 8, "LIST_JSAS": 8, "GET_JSA_DETAILS": 8, "UPDATE_JSA": 8, "DELETE_JSA": 8,
    "MANAGE_JSA_STEPS": 8, "LINK_JSA_PERMIT": 8,

    # Module 9: Training
    "RENEW_CERTIFICATE": 9, "CREATE_CERTIFICATE": 9, "LIST_CERTIFICATES": 9, "CREATE_TRAINING_COURSE": 9,

    # Module 10: PPE
    "CREATE_PPE_SUPPLY_ORDER": 10, "ISSUE_PPE": 10, "DELETE_PPE_TRANSACTION": 10, "ADD_PPE_ITEM": 10,
    "UPDATE_PPE_ITEM": 10, "DELETE_PPE_ITEM": 10, "LIST_PPE": 10, "UPDATE_PPE_STOCK": 10, "DELETE_PPE_MATRIX_RULE": 10,

    # Module 11: Fire Safety
    "LOG_FIRE_INSPECTION": 11, "INSPECT_FIXED_SAFETY_ASSET": 11, "ADD_FIRE_EQUIPMENT": 11,
    "LIST_FIRE_EQUIPMENT": 11, "DELETE_FIXED_SAFETY_ASSET": 11,
    "SERVICE_FIRE_EQUIPMENT": 11, "GET_FIRE_READINESS_REPORT": 11, "GET_FIRE_INSPECTION_SCHEDULE": 11,
    "GET_FIRE_EQUIPMENT_DETAIL": 11, "GET_FIRE_ATTENTION_LIST": 11, "GET_FIRE_COVERAGE_BY_ZONE": 11,
    "GET_FIRE_EQUIPMENT_STATS": 11,

    # Module 12: Hazmat
    "ADD_CHEMICAL": 12, "LIST_CHEMICALS": 12, "GET_CHEMICAL_DETAILS": 12, "DELETE_CHEMICAL": 12,
    "CHECK_CHEMICAL_STORAGE": 12, "GET_MSDS": 12,

    # Module 13: Medical
    "RECORD_MEDICAL_EXAM": 13, "LIST_MEDICAL_EXAMS": 13,

    # Module 14: AI & IoT
    "ADD_IOT_SENSOR": 14, "LIST_AI_IOT": 14,

    # Module 15: Security & System Architecture
    "LIST_SECURITY_ROLES": 15, "MANAGE_USERS": 15, "MANAGE_INTEGRATIONS": 15,
    "GET_SYSTEM_ARCHITECTURE": 15, "GET_SERVICE_HEALTH": 15, "SEARCH_RAG_KNOWLEDGE": 15,
}

INTENT_TO_TOOL_MAP: Dict[str, List[str]] = {
    # Module 1: Master Data
    "LIST_DEPARTMENTS": ["list_departments", "list_zones", "get_department_details", "get_department_zones_summary"],
    "GET_DEPARTMENT_DETAILS": ["get_department_details", "list_departments", "list_zones"],
    "CREATE_DEPARTMENT": ["create_department", "list_departments"],
    "UPDATE_DEPARTMENT": ["update_department", "list_departments"],
    "DELETE_DEPARTMENT": ["delete_department", "list_departments"],
    "LIST_ZONES": ["list_zones", "list_departments", "get_zone_details"],
    "GET_ZONE_DETAILS": ["get_zone_details", "list_zones", "list_departments"],
    "CREATE_ZONE": ["create_zone", "list_zones", "list_departments"],
    "UPDATE_ZONE": ["update_zone", "list_zones"],
    "DELETE_ZONE": ["delete_zone", "list_zones"],
    "GET_DEPARTMENT_ZONES_SUMMARY": ["get_department_zones_summary", "list_departments", "list_zones"],
    "LIST_EMPLOYEES": ["list_employees", "get_employee_info"],
    "CREATE_EMPLOYEE": ["create_employee", "list_employees"],
    "UPDATE_EMPLOYEE": ["update_employee", "list_employees"],
    "GET_EMPLOYEE_INFO": ["get_employee_info", "list_certificates"],

    # Module 2: Dashboard & Reports
    "GET_DASHBOARD_SUMMARY": ["get_dashboard_summary", "get_monthly_kpis", "get_safety_scores"],
    "REFRESH_DASHBOARD": ["refresh_dashboard", "get_dashboard_summary", "get_safety_scores"],
    "GET_MONTHLY_KPIS": ["get_monthly_kpis", "get_dashboard_summary"],
    "GET_SAFETY_SCORES": ["get_safety_scores", "list_zones"],
    "GET_TRIR_METRICS": ["get_trir_ltifr_metrics", "get_dashboard_summary", "get_monthly_kpis"],
    "LIST_AUDIT_LOGS": ["list_audit_logs", "verify_audit_log_chain"],
    "VERIFY_AUDIT_LOG": ["verify_audit_log_chain", "list_audit_logs"],
    "GET_SECURITY_AUDIT_SUMMARY": ["get_security_audit_summary", "list_audit_logs", "list_users"],
    "EXPORT_REPORTS_EXCEL": ["export_reports_excel", "get_dashboard_summary", "get_monthly_kpis"],
    "EXPORT_REPORTS_PDF": ["export_reports_pdf", "get_dashboard_summary"],
    "SEND_REPORT_TO_MANAGEMENT": ["send_report_to_management", "export_reports_excel", "get_dashboard_summary"],
    "GENERATE_CUSTOM_REPORT": ["generate_custom_report", "export_reports_excel", "list_incidents", "list_permits"],
    "OPEN_READY_REPORT": ["open_ready_report", "get_dashboard_summary", "get_fire_readiness_report", "list_certificates"],
    "SCHEDULE_REPORT": ["schedule_report", "send_report_to_management"],

    # Module 3: Incidents
    "CREATE_INCIDENT": ["create_incident", "list_incidents"],
    "EXPORT_INCIDENTS_EXCEL": ["export_incidents_excel", "list_incidents"],
    "GENERATE_REPORT_TEMPLATE": ["generate_external_report_template", "get_incident_details", "list_incidents"],
    "MANAGE_RCA": ["create_incident_rca", "get_incident_rca", "get_root_causes_summary"],
    "GET_ROOT_CAUSES": ["get_root_causes_summary", "get_incident_rca"],
    "LOG_SAFETY_OBSERVATION": ["log_safety_observation", "list_incidents"],
    "LIST_INCIDENTS": ["list_incidents", "get_dashboard_summary"],
    "GET_INCIDENT_DETAILS": ["get_incident_details", "get_incident_rca"],
    "UPDATE_INCIDENT": ["update_incident_status", "update_incident"],

    # Module 4: Permits & SIMOPS
    "CREATE_PERMIT": ["create_permit", "list_permits", "check_simops_conflicts"],
    "APPROVE_PERMIT": ["update_permit_status", "get_permit_details", "list_permits"],
    "SUSPEND_PERMIT": ["update_permit_status", "get_permit_details", "list_permits"],
    "CLOSE_PERMIT": ["update_permit_status", "close_all_permits", "get_permit_details", "list_permits"],
    "CLOSE_ALL_PERMITS": ["close_all_permits", "update_permit_status", "list_permits"],
    "LIST_PERMITS": ["list_permits", "check_simops_conflicts"],
    "GET_PERMIT_DETAILS": ["get_permit_details", "list_permits", "check_simops_conflicts"],
    "UPDATE_PERMIT": ["update_permit", "update_permit_status", "get_permit_details"],
    "DELETE_PERMIT": ["delete_permit", "delete_record", "update_permit_status", "list_permits"],
    "CHECK_SIMOPS": ["check_simops_conflicts", "list_permits"],

    # Module 5: Inspections
    "SCHEDULE_INSPECTION": ["schedule_safety_inspection", "list_inspections", "submit_inspection_walk"],
    "SUBMIT_INSPECTION_WALK": ["submit_inspection_walk", "create_inspection_finding", "schedule_safety_inspection", "list_inspections"],
    "LIST_INSPECTIONS": ["list_inspections", "schedule_safety_inspection", "submit_inspection_walk", "get_inspection_stats", "list_inspection_findings"],
    "GET_INSPECTION_DETAILS": ["get_inspection_details", "list_inspection_findings", "update_inspection_status", "list_inspections"],
    "GET_INSPECTION_STATS": ["get_inspection_stats", "list_inspections", "schedule_safety_inspection"],
    "CREATE_INSPECTION_FINDING": ["create_inspection_finding", "update_inspection_finding", "list_inspection_findings"],
    "UPDATE_INSPECTION": ["update_inspection_status", "update_inspection", "schedule_safety_inspection", "list_inspections"],
    "UPDATE_INSPECTION_FINDING": ["update_inspection_finding", "create_inspection_finding", "list_inspection_findings"],
    "DELETE_INSPECTION": ["delete_inspection", "delete_record", "list_inspections"],
    "DELETE_INSPECTION_FINDING": ["delete_inspection_finding", "delete_record", "list_inspection_findings"],
    "GENERATE_INSPECTION_CHECKLIST": ["generate_inspection_checklist", "list_inspection_templates", "schedule_safety_inspection"],

    # Module 6: CAPA
    "CREATE_CAPA": ["create_capa", "list_capas"],
    "LIST_CAPAS": ["list_capas", "list_overdue_capas"],
    "UPDATE_CAPA": ["update_capa_status", "list_capas"],

    # Module 7: Risk Register
    "CREATE_RISK": ["create_risk_assessment", "list_risk_register"],
    "LIST_RISK": ["list_risk_register", "get_risk_matrix", "get_high_risk_hazards"],
    "GET_RISK_DETAILS": ["get_risk_assessment_details", "list_risk_register"],
    "UPDATE_RISK": ["update_risk_assessment", "list_risk_register"],
    "DELETE_RISK": ["delete_risk_assessment", "list_risk_register"],
    "CALCULATE_RESIDUAL_RISK": ["calculate_residual_risk", "get_risk_matrix"],
    "GET_HIGH_RISK_HAZARDS": ["get_high_risk_hazards", "list_risk_register", "get_risk_matrix"],

    # Module 8: JSA
    "CREATE_JSA": ["create_jsa", "list_jsas"],
    "LIST_JSAS": ["list_jsas", "get_jsa_details"],
    "GET_JSA_DETAILS": ["get_jsa_details", "list_jsas"],
    "UPDATE_JSA": ["update_jsa", "list_jsas"],
    "DELETE_JSA": ["delete_jsa", "list_jsas"],
    "MANAGE_JSA_STEPS": ["add_jsa_step", "update_jsa_step", "delete_jsa_step", "get_jsa_details"],
    "LINK_JSA_PERMIT": ["link_jsa_permit", "unlink_jsa_permit", "list_available_permits_for_jsa"],

    # Module 9: Training
    "RENEW_CERTIFICATE": ["update_certificate_status", "update_certificate", "list_certificates"],
    "CREATE_CERTIFICATE": ["create_certificate", "list_training_courses"],
    "LIST_CERTIFICATES": ["list_certificates", "get_overdue_training"],
    "CREATE_TRAINING_COURSE": ["create_training_course", "list_training_courses"],

    # Module 10: PPE
    "CREATE_PPE_SUPPLY_ORDER": ["create_ppe_supply_order", "get_ppe_stock_status", "list_ppe_inventory"],
    "ISSUE_PPE": ["create_ppe_transaction", "get_ppe_stock_status", "list_ppe_inventory"],
    "DELETE_PPE_TRANSACTION": ["delete_ppe_transaction", "list_ppe_transactions"],
    "ADD_PPE_ITEM": ["add_ppe_item", "list_ppe_inventory"],
    "UPDATE_PPE_ITEM": ["update_ppe_item", "update_ppe_stock", "list_ppe_inventory"],
    "DELETE_PPE_ITEM": ["delete_ppe_item", "list_ppe_inventory"],
    "LIST_PPE": ["list_ppe_inventory", "get_ppe_stock_status", "list_ppe_matrix"],
    "UPDATE_PPE_STOCK": ["update_ppe_stock", "list_ppe_inventory"],
    "DELETE_PPE_MATRIX_RULE": ["delete_ppe_matrix_rule", "list_ppe_matrix"],

    # Module 11: Fire Safety
    "LOG_FIRE_INSPECTION": ["log_fire_inspection", "get_fire_equipment_detail", "list_fire_equipment"],
    "SERVICE_FIRE_EQUIPMENT": ["service_fire_equipment", "update_fire_equipment", "get_fire_attention_list", "list_fire_equipment"],
    "GET_FIRE_READINESS_REPORT": ["get_fire_readiness_report", "get_fire_equipment_stats", "list_fire_equipment"],
    "GET_FIRE_INSPECTION_SCHEDULE": ["get_fire_inspection_schedule", "list_fire_inspections", "list_fire_equipment"],
    "GET_FIRE_EQUIPMENT_DETAIL": ["get_fire_equipment_detail", "log_fire_inspection", "list_fire_equipment"],
    "GET_FIRE_ATTENTION_LIST": ["get_fire_attention_list", "get_expired_fire_equipment", "service_fire_equipment"],
    "GET_FIRE_COVERAGE_BY_ZONE": ["get_fire_coverage_by_zone", "get_fire_readiness_report", "list_fire_equipment"],
    "GET_FIRE_EQUIPMENT_STATS": ["get_fire_equipment_stats", "get_fire_readiness_report", "list_fire_equipment"],
    "INSPECT_FIXED_SAFETY_ASSET": ["record_fixed_safety_asset_inspection", "update_fixed_safety_asset", "list_fixed_safety_assets"],
    "ADD_FIRE_EQUIPMENT": ["add_fire_equipment", "add_fixed_safety_asset", "list_fire_equipment"],
    "LIST_FIRE_EQUIPMENT": ["list_fire_equipment", "get_fire_equipment_detail", "get_expired_fire_equipment", "list_fixed_safety_assets"],
    "DELETE_FIXED_SAFETY_ASSET": ["delete_fixed_safety_asset", "list_fixed_safety_assets"],

    # Module 12: Chemicals
    "ADD_CHEMICAL": ["add_chemical", "list_chemicals", "get_chemical_details"],
    "LIST_CHEMICALS": ["list_chemicals", "get_chemical_details", "get_chemical_compatibility", "check_chemical_storage_safety"],
    "GET_CHEMICAL_DETAILS": ["get_chemical_details", "get_chemical_emergency_guide", "get_msds_sheet", "list_chemicals"],
    "UPDATE_CHEMICAL": ["update_chemical", "update_chemical_stock", "get_chemical_details", "list_chemicals"],
    "DELETE_CHEMICAL": ["delete_chemical", "list_chemicals"],
    "CHECK_CHEMICAL_STORAGE": ["check_chemical_storage_safety", "get_chemical_compatibility", "list_chemicals"],
    "GET_MSDS": ["get_msds_sheet", "list_sds_records", "get_chemical_emergency_guide", "get_chemical_details"],
    "EMERGENCY_GUIDE": ["get_chemical_emergency_guide", "get_msds_sheet", "get_chemical_details", "list_chemicals"],
    "SDS_ARCHIVE": ["list_sds_records", "get_msds_sheet", "list_chemicals"],

    # Module 13: Medical
    "RECORD_MEDICAL_EXAM": ["record_medical_exam", "schedule_medical_exam", "list_medical_exams", "get_employee_info", "update_medical_exam"],
    "LIST_MEDICAL_EXAMS": ["list_medical_exams", "list_occupational_exposures", "list_wearable_devices"],

    # Module 14: AI & IoT
    "ADD_IOT_SENSOR": ["add_iot_sensor", "list_iot_sensors"],
    "LIST_AI_IOT": ["list_iot_sensors", "get_recent_sensor_alerts", "list_cameras", "get_recent_ai_events"],

    # Module 15: Security, Architecture & Governance
    "LIST_SECURITY_ROLES": ["list_security_roles", "get_role_permissions", "list_users"],
    "MANAGE_USERS": ["list_users", "get_user_details", "create_user_role_assignment", "update_user_role"],
    "MANAGE_INTEGRATIONS": ["list_integrations", "get_integration_status", "sync_integration_connector", "test_integration_connection", "update_integration_config", "get_integration_sync_logs"],
    "GET_SYSTEM_ARCHITECTURE": ["get_system_architecture", "get_service_health_status", "get_database_metrics", "get_api_endpoints_catalog"],
    "GET_SERVICE_HEALTH": ["get_service_health_status", "get_database_metrics"],
    "SEARCH_RAG_KNOWLEDGE": ["search_hse_knowledge"],
}


def get_keywords_for_module(module_num: int) -> List[str]:
    """Returns all unique keywords and phrases registered for a given module ID (1 to 15)."""
    intents_in_mod = [intent for intent, mod_id in INTENT_TO_MODULE_MAP.items() if mod_id == module_num]
    keywords: set[str] = set()
    for intent in intents_in_mod:
        keywords.update(HSE_INTENTS_KEYWORDS.get(intent, []))
    return sorted(list(keywords))


def search_keyword_across_modules(keyword: str) -> List[Dict[str, Any]]:
    """Finds all modules and intents that contain a matching keyword."""
    if not keyword:
        return []
    clean = normalize_text(keyword)
    matches = []
    for intent, kw_list in HSE_INTENTS_KEYWORDS.items():
        matched_kw = []
        for kw in kw_list:
            if clean in normalize_text(kw):
                matched_kw.append(kw)
        if matched_kw:
            mod_id = INTENT_TO_MODULE_MAP.get(intent, 0)
            matches.append({
                "module_id": mod_id,
                "module_info": MODULE_METADATA.get(mod_id, {}),
                "intent": intent,
                "matched_keywords": matched_kw
            })
    return matches
