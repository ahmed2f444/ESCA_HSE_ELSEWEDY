import re
import json
import uuid
from sqlalchemy.orm import Session
from app.llm_client import chat_completion
from app.schemas import ToolCallTrace, AskResponse
from app.tools.definitions import TOOLS, LOCAL_TOOLS
from app.tools.handlers import HANDLERS
from app.tools.rbac import filter_tools_for_role, check_tool_access, normalize_role


# ── Fallback table formatter (used when LLM synthesis fails) ──────────────────
_ARABIC_HEADERS = {
    "incident_id": "رقم الحادث", "incident_status_id": "رقم الحالة", "name": "الاسم/الحالة",
    "status": "الحالة", "severity": "الخطورة", "title": "العنوان", "description": "الوصف",
    "reported_at": "تاريخ البلاغ", "zone_id": "المنطقة", "zone_name": "اسم المنطقة", "lost_days": "أيام الفقد",
    "employee_id": "رقم الموظف", "display_name": "اسم الموظف", "employee_name": "اسم الموظف",
    "due_date": "تاريخ الاستحقاق", "days_overdue": "أيام التأخير", "priority": "الأولوية", "capa_id": "رقم الإجراء",
    "permit_id": "رقم التصريح", "permit_type": "نوع التصريح", "risk_level": "مستوى الخطورة",
    "balance_qty": "الرصيد", "item_code": "كود الصنف", "name_ar": "الاسم (عربي)", "name_en": "الاسم (إنجليزي)",
    "category": "التصنيف", "month": "الشهر", "trir": "TRIR", "ltifr": "LTIFR",
    "hours_worked": "ساعات العمل", "count": "العدد", "total_count": "إجمالي السجلات",
    "returned_count": "السجلات المعروضة", "operation": "نوع العملية",
    "success": "النجاح", "message": "الرسالة", "trade_name": "الاسم التجاري",
    "chemical_name": "الاسم الكيميائي", "cas_number": "رقم CAS", "standard": "المعيار / المواصفة",
    "clause": "البند", "title_ar": "عنوان البند", "content_ar": "النص العربي",
    "certificate_id": "رقم الشهادة", "certificate_code": "كود الشهادة",
    "course_id": "رقم الدورة", "course_name": "اسم الدورة التدريبية", "course": "الدورة التدريبية",
    "issue_date": "تاريخ الإصدار", "renewal_date": "تاريخ التجديد",
    "new_expiry_date": "تاريخ الانتهاء الجديد", "expiry_date": "تاريخ انتهاء الصلاحية",
    "expiry_time": "وقت انتهاء الصلاحية", "full_expiry": "تاريخ ووقت الانتهاء",
    "validity_duration": "مدة الصلاحية المعتمدة",
    "days_remaining": "الأيام المتبقية", "days_to_expiry": "الأيام المتبقية للصلاحية",
    "days_remaining_text": "الأيام المتبقية", "days_remaining_ar": "الأيام المتبقية",
    "status_ar": "الحالة المعتمدة", "job_title": "المسمى الوظيفي", "department_name": "اسم القسم",
    "manager_name": "اسم المدير", "hse_contact_name": "مسؤول السلامة", "max_occupancy": "السعة القصوى",
    "zone_type": "نوع المنطقة", "score_pct": "نسبة النتيجة %", "safety_score": "درجة السلامة",
    "compliance_status": "حالة الامتثال", "inspection_id": "رقم التفتيش", "inspection_type": "نوع التفتيش",
    "scheduled_at": "الموعد المجدول", "completed_at": "تاريخ الإنجاز", "finding_id": "رقم الملاحظة",
    "hazard": "الخطر المحتمل", "activity": "النشاط / المهمة", "inherent_score": "التقييم الأولي",
    "residual_score": "الخطر المتبقي", "controls": "إجراءات التحكم", "jsa_id": "رقم تحليل المهام",
    "task_name": "اسم المهمة", "permit_required": "يتطلب تصريح عمل", "fitness_result": "نتيجة الكفاءة الطبية",
    "restriction_summary": "القيود الطبية", "exam_id": "رقم الفحص الطبي", "protocol_name": "البروتوكول الطبي",
    "sensor_type": "نوع الحساس", "safe_max": "الحد الآمن الأقصى", "warning_max": "حد التحذير",
    "equipment_id": "رقم المعدة", "asset_type": "نوع الأصل/المعدة", "subtype": "النوع الفرعي",
    "location_detail": "الموقع بالتفصيل", "next_inspection_date": "تاريخ الفحص القادم",
    "asset_summary_id": "رقم الأصل الثابت", "total_qty": "إجمالي العدد", "operational_qty": "العدد الجاهز للعمل",
    "audit_id": "رقم التدقيق", "occurred_at": "تاريخ ووقت العملية", "actor_id": "المستخدم/الفاعل",
    "action": "الإجراء المنفذ", "entity_type": "نوع الكيان", "entity_id": "معرف السجل",
}

def _format_fallback_table(result_data: any, question: str = "") -> str:
    """Builds a readable Arabic Markdown table from raw query results when the LLM synthesis fails."""
    rows = []
    if isinstance(result_data, dict):
        if result_data.get("success"):
            lines = ["### ✅ تم تنفيذ العملية بنجاح:\n"]
            for k, v in result_data.items():
                label = _ARABIC_HEADERS.get(k, k)
                lines.append(f"- **{label}**: `{v}`")
            return "\n".join(lines)
        if "results" in result_data and isinstance(result_data["results"], list):
            rows = result_data["results"]
        else:
            rows = result_data.get("rows", [])
            if not rows and not any(k in result_data for k in ("rows", "error", "results")):
                lines = [f"**نتائج الاستعلام:**\n"]
                for k, v in result_data.items():
                    label = _ARABIC_HEADERS.get(k, k)
                    lines.append(f"- **{label}**: {v}")
                return "\n".join(lines)
    elif isinstance(result_data, list):
        rows = result_data

    if not rows:
        return "لم يتم العثور على سجلات مطابقة في قاعدة البيانات."

    # Build markdown table
    if isinstance(rows[0], dict):
        cols = list(rows[0].keys())[:8]  # Limit columns for compact display
        headers = [_ARABIC_HEADERS.get(c, c) for c in cols]
        table_lines = ["| " + " | ".join(headers) + " |"]
        table_lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for row in rows[:30]:
            vals = [str(row.get(c, "-")).replace("\n", " ") for c in cols]
            table_lines.append("| " + " | ".join(vals) + " |")
        summary = f"\n\n**الإجمالي:** {len(rows)} سجل من قاعدة البيانات."
        return "\n".join(table_lines) + summary
    else:
        return "\n".join([f"- {r}" for r in rows[:30]])


SYSTEM_PROMPT = """You are ESCA HSE AI Assistant — an expert Health, Safety & Environment AI with direct live access to the MySQL database (135 tables) for Elsewedy Cables (ESCA).

CAPABILITIES (All 15 ESCA HSE Modules):
1. RAG & Standards: ISO 45001:2018 clauses, OSHA standards (1910/1926), Elsewedy 10 Safety Golden Rules, chemical GHS classifications, gas limits via `search_hse_knowledge`.
2. Live Database Inquiries: Direct query access across all 15 modules:
   - Master Data: `list_departments`, `list_zones`, `list_employees`, `get_employee_info`
   - Executive Dashboard & KPIs: `get_dashboard_summary`, `get_monthly_kpis`, `get_safety_scores`, `list_audit_logs`
   - Incidents & RCA: `list_incidents`, `get_incident_details`, `get_incident_rca`
   - Permits to Work & SIMOPS: `list_permits`, `get_permit_details`, `check_simops_conflicts`
   - Inspections & Findings: `list_inspections`, `list_inspection_findings`, `list_inspection_templates`
   - CAPA: `list_capas`, `list_overdue_capas`, `get_capa_details`
   - Risk Register & HIRA: `list_risk_register`, `get_risk_matrix`
   - Job Safety Analysis: `list_jsas`, `get_jsa_details`
   - Training & Competency: `list_certificates`, `list_training_courses`, `get_overdue_training`
   - PPE Management: `list_ppe_inventory`, `get_ppe_stock_status`, `list_ppe_matrix`, `list_ppe_transactions`
   - Fire Safety & Fixed Assets: `list_fire_equipment`, `get_expired_fire_equipment`, `list_fire_inspections`, `list_fixed_safety_assets`
   - HazMat & Chemicals: `list_chemicals`, `get_chemical_compatibility`
   - Occupational Health: `list_medical_exams`, `list_occupational_exposures`, `list_wearable_devices`
   - AI Vision & IoT Sensors: `list_iot_sensors`, `get_recent_sensor_alerts`, `list_cameras`, `get_recent_ai_events`
   - Security & RBAC: `list_security_roles`, `list_integrations`
3. Full CRUD Mutations:
   - CREATE: `create_employee`, `create_incident`, `log_safety_observation`, `create_permit`, `schedule_safety_inspection`, `create_inspection_finding`, `create_capa`, `create_risk_assessment`, `create_jsa`, `create_training_course`, `create_certificate`, `add_ppe_item`, `create_ppe_transaction`, `add_fire_equipment`, `add_fixed_safety_asset`, `log_fire_inspection`, `add_chemical`, `record_medical_exam`, `schedule_medical_exam`, `add_iot_sensor`, `log_ai_event`.
   - UPDATE: `update_employee`, `update_incident_status`, `update_incident`, `update_permit_status`, `update_inspection_status`, `update_capa_status`, `update_risk_assessment`, `update_jsa`, `update_training_course`, `update_certificate_status`, `update_ppe_stock`, `update_ppe_matrix`, `update_fire_equipment`, `update_fixed_safety_asset`, `update_chemical_stock`, `update_chemical`, `update_medical_exam`, `update_iot_sensor`.
   - DELETE/CANCEL: `delete_record`, `cancel_entity`, `execute_database_dml`.

OPERATIONAL RULES & TOOL INVOCATIONS:
1. When asked to issue PPE (e.g. "صرف 2 خوذة سلامة للموظف أحمد سامي"): ALWAYS invoke `create_ppe_transaction(ppe_item_id="خوذة سلامة", employee_id="أحمد سامي", quantity=2)`.
2. When asked to schedule an inspection (e.g. "جدول فحص سلامة روتيني لمنطقة الإنتاج رقم 2"): ALWAYS invoke `schedule_safety_inspection(inspection_type="ROUTINE_WALK", zone_id=2, scheduled_in_days=7)`.
3. When asked to log a fire inspection (e.g. "سجل فحص طفاية الحريق رقم 1 وكانت النتيجة ناجحة"): ALWAYS invoke `log_fire_inspection(equipment_id=1, result="PASS", pressure_ok=True, hose_ok=True)`.
4. When asked to register a risk assessment (e.g. "سجل تقييم مخاطر جديد لخطر التعرض لغاز H2S"): ALWAYS invoke `create_risk_assessment(hazard="التعرض لغاز كبريتيد الهيدروجين", activity="صيانة البيارات", controls="نظام LOTO وفحص الغازات", zone_id=4)`.
5. When asked to log a safety observation (e.g. "سجل ملاحظة سلوك غير آمن: عامل بدون حزام"): ALWAYS invoke `log_safety_observation(description="عامل يعمل على ارتفاع بدون ربط حزام الأمان في عنبر 3", observation_type="UNSAFE_ACT", zone_id=3)`.
6. When asked to add chemical (e.g. "أضف مادة كيميائية جديدة: إيثانول صناعي"): ALWAYS invoke `add_chemical(trade_name="Industrial Ethanol", chemical_name="إيثانول صناعي", cas_number="64-17-5", quantity=500, unit="Liters", zone_id=4)`.
7. When asked to add fire equipment (e.g. "أضف طفاية حريق جديدة نوع CO2"): ALWAYS invoke `add_fire_equipment(asset_type="EXTINGUISHER", subtype="CO2_6KG", location_detail="بجوار اللوحة الرئيسية في عنبر 2", vendor="Bavaria Egypt")`.
8. When asked to create JSA (e.g. "انشئ تحليل سلامة مهام JSA لعمليات اللحام في الأماكن المغلقة"): ALWAYS invoke `create_jsa(task_name="Welding inside confined tank", zone_id=1, permit_required=True, permit_type="CONFINED_SPACE")`.
9. When asked to record medical exam (e.g. "سجل فحص كفاءة طبية للموظف أحمد سامي وكانت النتيجة لائق"): ALWAYS invoke `record_medical_exam(employee_id="أحمد سامي", fitness_result="FIT")`.
10. When asked to add IoT sensor (e.g. "أضف مستشعر غازات VOC في عنبر 2"): ALWAYS invoke `add_iot_sensor(sensor_type="VOC", zone_id=2, unit="ppm", safe_max=50.0, warning_max=80.0)`.
11. CERTIFICATE RENEWAL WORKFLOW & ACCREDITED DURATION:
   - When a user asks to renew a certificate (e.g. "renew this certificate", "TRN-063 renew", "جدد هذه الشهادة", "جدد شهادة عمر خالد رقم TRN-063", "renew course TRN-063"):
     - ALWAYS invoke `update_certificate_status(certificate_id=...)` with `status="VALID"`.
     - Standard Renewal Duration: If the user did not specify a duration, pass `expiry_date="1 year"` or omit it to automatically apply the accredited course validity period (+1 Year / 12 months / 365 days or +2 Years / 24 months). NEVER invent arbitrary short dates (like tomorrow, 2 days, or end of month).
     - Custom Duration: If the user specifies "+1 year", "+2 years", "6 months", or a specific future date (e.g. "2027-08-29"), pass that as `expiry_date`.
     - Default Expiration Time: "23:59" unless a specific time is given.
     - Arabic Terminology: In Arabic confirmation tables, ALWAYS write "الأيام المتبقية" (Remaining Days). Strictly NEVER write "الأيدي المتبقية".
     - Presentation: Structure the renewal confirmation table with:
       | البيان | التفاصيل |
       | رقم الشهادة | TRN-063 |
       | اسم الموظف | عمر خالد |
       | اسم الدورة | السلامة العامة |
       | تاريخ الانتهاء الجديد | 2027-08-29 |
       | وقت الانتهاء | 23:59 |
       | الحالة | سارية ومعتمدة (VALID) |
       | الأيام المتبقية | 365 يوم |
     - When renewed for 1+ years (365 days), provide a positive HSE confirmation confirming the employee is certified and the competency matrix is updated. Do NOT trigger false 48-hour expiration warnings.
12. Result Formatting:
   - When a CRUD operation succeeds, prominently state the confirmation, entity type, created/updated ID, and status.
   - For query results, present data in clean, well-aligned Markdown tables with Arabic column headers, followed by bullet-point insights and proactive HSE recommendations.
   - Never output raw SQL code (e.g. SELECT/INSERT) or internal JSON blobs in conversational responses.
   - Reply in the user's language (Arabic by default, English if asked in English)."""


LOCAL_SYSTEM_PROMPT = """You are ESCA HSE AI Assistant with direct live MySQL access and full RAG & CRUD operation capabilities across all 15 factory safety modules.

FEW-SHOT EXAMPLES:
User: "TRN-063 renew this certificate" -> Tool: update_certificate_status(certificate_id=63, status="VALID", expiry_date="1 year")
User: "جدد شهادة عمر خالد TRN-063" -> Tool: update_certificate_status(certificate_id=63, status="VALID", expiry_date="1 year")
User: "renew it for 2 years" -> Tool: update_certificate_status(certificate_id=63, status="VALID", expiry_date="2 years")
User: "renew certificate TRN-085 until 2027-08-29 at 5:30 pm" -> Tool: update_certificate_status(certificate_id=85, expiry_date="2027-08-29", expiry_time="5:30 PM", status="VALID")
User: "صرف 2 خوذة سلامة للموظف أحمد سامي" -> Tool: create_ppe_transaction(ppe_item_id="خوذة سلامة", employee_id="أحمد سامي", quantity=2)
User: "جدول فحص سلامة روتيني لمنطقة الإنتاج رقم 2 الأسبوع القادم" -> Tool: schedule_safety_inspection(inspection_type="ROUTINE_WALK", zone_id=2, scheduled_in_days=7)
User: "سجل فحص طفاية الحريق رقم 1 وكانت النتيجة ناجحة والضغط سليم" -> Tool: log_fire_inspection(equipment_id=1, result="PASS", pressure_ok=True, hose_ok=True)
User: "سجل تقييم مخاطر جديد لخطر التعرض لغاز كبريتيد الهيدروجين" -> Tool: create_risk_assessment(hazard="التعرض لغاز كبريتيد الهيدروجين", activity="صيانة البيارات", controls="نظام LOTO وفحص الغازات", zone_id=4)
User: "سجل ملاحظة سلوك غير آمن: عامل بدون حزام أمان في عنبر 3" -> Tool: log_safety_observation(description="عامل يعمل على ارتفاع بدون ربط حزام الأمان في عنبر 3", observation_type="UNSAFE_ACT", zone_id=3)
User: "أضف مادة كيميائية جديدة: إيثانول صناعي ورقم CAS 64-17-5" -> Tool: add_chemical(trade_name="Industrial Ethanol", chemical_name="إيثانول صناعي", cas_number="64-17-5", quantity=500, unit="Liters", zone_id=4)
User: "أضف طفاية حريق جديدة نوع CO2 سعة 6 كجم بجوار اللوحة الرئيسية" -> Tool: add_fire_equipment(asset_type="EXTINGUISHER", subtype="CO2_6KG", location_detail="بجوار اللوحة الرئيسية في عنبر 2", vendor="Bavaria Egypt")
User: "انشئ تحليل سلامة مهام JSA لأعمال صيانة الكابلات ذات الجهد العالي" -> Tool: create_jsa(task_name="High Voltage Cable Maintenance", zone_id=2, permit_required=True, permit_type="ELECTRICAL")
User: "سجل فحص طبي دوري للموظف عمر خالد بنتيجة لائق" -> Tool: record_medical_exam(employee_id="عمر خالد", fitness_result="FIT")
User: "أضف مستشعر غاز VOC في عنبر 2 بحد آمن 50 ppm" -> Tool: add_iot_sensor(sensor_type="VOC", zone_id=2, unit="ppm", safe_max=50.0, warning_max=80.0)
User: "اعرض ملخص لوحة القيادة ومؤشرات السلامة" -> Tool: get_dashboard_summary()
User: "هل يوجد تعارض بين تصاريح العمل في عنبر 1؟" -> Tool: check_simops_conflicts(zone_id=1)
User: "ما هي اشتراطات الدخول للأماكن المغلقة حسب OSHA؟" -> Tool: search_hse_knowledge(query="confined space gas limits OSHA")
User: "انشئ بلاغ حادث جديد: تسريب زيت في عنبر 2" -> Tool: create_incident(title="تسريب زيت", description="تسريب زيت في عنبر 2", zone_id=2, severity="MODERATE", incident_type="UNSAFE_CONDITION")
User: "اعتمد تصريح العمل رقم 10" -> Tool: update_permit_status(permit_id=10, status="APPROVED", reason_or_note="تم الفحص والاعتماد")
User: "ما هي إجراءات CAPA المتأخرة التي لم تكتمل؟" -> Tool: list_overdue_capas()
User: "List all active electronic work permits ePTW" -> Tool: list_permits(status="ACTIVE")

RULES:
1. Always invoke the matching tool for queries, standards lookups, or CRUD operations.
2. For certificate renewals, ALWAYS default to accredited course validity (+1 Year / +2 Years). Never invent arbitrary 1-2 day short dates.
3. In Arabic confirmation tables, ALWAYS use "الأيام المتبقية" (Remaining Days) and never use "الأيدي المتبقية".
4. Confirm CRUD operations with ID, entity details, and new status."""


def _get_dynamic_system_prompt(model_mode: str = "auto") -> str:
    from datetime import date, datetime, timedelta
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    next_year_str = (date.today() + timedelta(days=365)).isoformat()

    base_prompt = LOCAL_SYSTEM_PROMPT if model_mode == "local" else SYSTEM_PROMPT
    time_context = (
        f"\n\nCURRENT DATE & TIME CONTEXT (LIVE):\n"
        f"- Today's current date: {today_str}\n"
        f"- Current local time: {now_str}\n"
        f"- Tomorrow's date: {tomorrow_str}\n"
        f"- Next year date: {next_year_str}\n"
        f"ALWAYS evaluate dates relative to today ({today_str}). Tomorrow ({tomorrow_str}) is a valid FUTURE date."
    )
    return base_prompt + time_context


SESSION_HISTORIES: dict[str, list[dict]] = {}


def _filter_local_tools(question: str, all_local_tools: list[dict], history: list = None) -> list[dict]:
    """Dynamically narrows down tools using the high-performance NLP keyword parser library."""
    from app.nlp.keyword_parser import get_recommended_tools_for_prompt

    # Use comprehensive multilingual parser
    matched_tools = get_recommended_tools_for_prompt(question, all_local_tools)

    # Check previous conversation context if current turn is very brief (e.g. "لسنة قادمة" or "2027-08-29")
    if len(question.strip().split()) <= 4 and history:
        prev_user_msgs = [h.get("content", "") for h in history if isinstance(h, dict) and h.get("role") == "user"]
        if prev_user_msgs:
            combined_context = f"{prev_user_msgs[-1]} {question}"
            context_tools = get_recommended_tools_for_prompt(combined_context, all_local_tools)
            tool_names = {t["function"]["name"] for t in matched_tools}
            for t in context_tools:
                if t["function"]["name"] not in tool_names:
                    matched_tools.append(t)

    return matched_tools or all_local_tools


def _extract_text_tool_calls(text: str) -> list[dict]:
    """Extracts function calls if the LLM outputted tool calls in raw text format (XML pseudo-tags or JSON)."""
    if not text or not isinstance(text, str):
        return []

    calls = []
    json_block_patterns = [
        re.compile(r'<(?:tool_call|function_call)>(.*?)(?:</(?:tool_call|function_call)>|<(?:tool_call|function_call)/>|$)', re.DOTALL | re.IGNORECASE),
        re.compile(r'```(?:tool_call|json)\s*(\{.*?\})\s*```', re.DOTALL | re.IGNORECASE),
        re.compile(r'```(?:tool_call|json)\s*(\[.*?\])\s*```', re.DOTALL | re.IGNORECASE),
    ]

    for pattern in json_block_patterns:
        for match in pattern.finditer(text):
            block = match.group(1).strip()
            try:
                data = json.loads(block)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            name = item.get("name") or item.get("function") or item.get("tool")
                            raw_args = item.get("arguments") or item.get("parameters") or item.get("args") or {}
                            if isinstance(raw_args, str):
                                try:
                                    raw_args = json.loads(raw_args)
                                except Exception:
                                    raw_args = {"query": raw_args}
                            if name and isinstance(raw_args, dict):
                                calls.append({"name": str(name).strip(), "arguments": raw_args})
                elif isinstance(data, dict):
                    name = data.get("name") or data.get("function") or data.get("tool")
                    raw_args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except Exception:
                            raw_args = {"query": raw_args}
                    if name and isinstance(raw_args, dict):
                        calls.append({"name": str(name).strip(), "arguments": raw_args})
            except Exception:
                pass

    if calls:
        return calls

    # XML tag style: <function=name> or <function name="name">
    func_pattern = re.compile(
        r'<function(?:=|\s+name=)[\"\\\']?([a-zA-Z0-9_]+)[\"\\\']?>(.*?)(?:</function>|<function/>|$)',
        re.DOTALL | re.IGNORECASE
    )
    param_pattern = re.compile(
        r'<parameter(?:=|\s+name=)[\"\\\']?([a-zA-Z0-9_]+)[\"\\\']?>(.*?)(?:</parameter>|<parameter/>|$)',
        re.DOTALL | re.IGNORECASE
    )

    for f_match in func_pattern.finditer(text):
        func_name = f_match.group(1).strip()
        body = f_match.group(2).strip()
        args = {}
        param_matches = list(param_pattern.finditer(body))
        if param_matches:
            for p_match in param_matches:
                p_name = p_match.group(1).strip()
                p_val = p_match.group(2).strip()
                if p_val.lower() == 'true':
                    args[p_name] = True
                elif p_val.lower() == 'false':
                    args[p_name] = False
                elif p_val.isdigit():
                    args[p_name] = int(p_val)
                else:
                    try:
                        args[p_name] = json.loads(p_val)
                    except Exception:
                        args[p_name] = p_val
        else:
            try:
                parsed_json = json.loads(body)
                if isinstance(parsed_json, dict):
                    args = parsed_json
            except Exception:
                if body and func_name == 'run_read_only_query':
                    args = {'sql_query': body}
                elif body:
                    args = {'query': body}
        calls.append({"name": func_name, "arguments": args})

    return calls


def _sanitize_response_text(text: str) -> str:
    """Removes thinking tags, tool call blocks, and any stray XML tags from conversational output."""
    if not text or not isinstance(text, str):
        return ""
    cleaned = re.sub(r'<think>[\s\S]*?(?:</think>|$)', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'<tool_call>[\s\S]*?(?:</tool_call>|<tool_call/>|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<function_call>[\s\S]*?(?:</function_call>|<function_call/>|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<function[=\s][\s\S]*?(?:</function>|<function/>|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<parameter[=\s][\s\S]*?(?:</parameter>|<parameter/>|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</?(?:tool_call|function_call|function|parameter|think)[^>]*>', '', cleaned, flags=re.IGNORECASE)

    if not cleaned.strip() and "<think>" in text:
        think_match = re.search(r'<think>([\s\S]*?)(?:</think>|$)', text, flags=re.IGNORECASE)
        if think_match:
            cleaned = think_match.group(1).strip()
            cleaned = re.sub(r'</?(?:tool_call|function_call|function|parameter|think)[^>]*>', '', cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def _format_compact_payload(result_data: any) -> str:
    """Formats SQL / CRUD results into a compact JSON string."""
    if isinstance(result_data, dict):
        rows = result_data.get("rows") or result_data.get("results")
        if isinstance(rows, list) and len(rows) > 20:
            compact_data = dict(result_data)
            compact_data["rows"] = rows[:20]
            compact_data["note"] = f"Displaying top 20 of {len(rows)} records."
            payload = json.dumps(compact_data, default=str)
        else:
            payload = json.dumps(result_data, default=str)
    elif isinstance(result_data, list) and len(result_data) > 20:
        payload = json.dumps({
            "rows": result_data[:20],
            "total_count": len(result_data),
            "note": f"Displaying top 20 of {len(result_data)} records."
        }, default=str)
    else:
        payload = json.dumps(result_data, default=str)

    if len(payload) > 8000:
        payload = payload[:8000] + "..."
    return payload


def _extract_embedded_sql(text_content: str) -> str | None:
    """Extracts raw SQL SELECT query if the model mistakenly typed SQL in conversational text."""
    if not text_content:
        return None
    match = re.search(r"(SELECT\s+[\s\S]+?\s+FROM\s+[\w`]+[\s\S]*?)(?:;|\n\n|$)", text_content, re.IGNORECASE)
    if match:
        sql = match.group(1).strip().rstrip(";")
        return sql
    return None


def run_agent_loop(
    question: str,
    db: Session,
    session_id: str | None = None,
    model_mode: str = "auto",
    client_history: list[dict] | None = None,
    user_role: str | None = "HSE_MANAGER",
    user_id: str | int | None = "AI_USER",
) -> AskResponse:
    canonical_role = normalize_role(user_role)

    # Initialize session history
    if not session_id or session_id not in SESSION_HISTORIES:
        session_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        sys_msg = {
            "role": "system",
            "content": _get_dynamic_system_prompt(model_mode),
        }
        init_msgs = [sys_msg]
        if client_history:
            for item in client_history[-4:]:
                role = "assistant" if item.get("role") == "agent" else item.get("role", "user")
                text_val = item.get("text") or item.get("content") or ""
                if text_val:
                    init_msgs.append({"role": role, "content": text_val})
        SESSION_HISTORIES[session_id] = init_msgs
    else:
        if SESSION_HISTORIES[session_id] and SESSION_HISTORIES[session_id][0].get("role") == "system":
            SESSION_HISTORIES[session_id][0]["content"] = _get_dynamic_system_prompt(model_mode)

    history = SESSION_HISTORIES[session_id]

    # Bounded context window
    history_limit = 4 if model_mode == "local" else 9
    if len(history) > history_limit:
        history = [history[0]] + history[-(history_limit - 1):]
        SESSION_HISTORIES[session_id] = history

    messages = list(history)
    messages.append({"role": "user", "content": question})

    # Apply RBAC filtering on available tools
    role_allowed_tools = filter_tools_for_role(TOOLS, canonical_role)
    role_allowed_local_tools = filter_tools_for_role(LOCAL_TOOLS, canonical_role)

    traces: list[ToolCallTrace] = []
    max_loops = 3
    seen_tool_calls: set[str] = set()
    last_model_used = None
    last_successful_result = None

    for i in range(max_loops):
        current_tools = _filter_local_tools(question, role_allowed_tools, history=messages)
        current_local_tools = _filter_local_tools(question, role_allowed_local_tools, history=messages)

        response, model_used = chat_completion(
            messages=messages,
            tools=current_tools,
            local_tools=current_local_tools,
            tool_choice="auto",
            model_mode=model_mode,
        )
        last_model_used = model_used
        message = response.choices[0].message

        # Check if model emitted tool calls
        if not message.tool_calls:
            content = (message.content or "").strip()

            # 1. Check for text-based tool calls
            extracted_tool_calls = _extract_text_tool_calls(content)
            if extracted_tool_calls and i < max_loops - 1:
                tool_results_text = []
                for tc in extracted_tool_calls:
                    func_name = tc["name"]
                    args = tc.get("arguments", {})
                    dedup_key = f"{func_name}:{json.dumps(args, sort_keys=True)}"
                    if dedup_key in seen_tool_calls:
                        tool_results_text.append(f"Tool {func_name}({args}): Already executed in previous step.")
                        continue
                    seen_tool_calls.add(dedup_key)

                    # RBAC Check
                    is_auth, auth_reason = check_tool_access(canonical_role, func_name)
                    if not is_auth:
                        err_res = {"error": f"RBAC Access Denied: Role '{canonical_role}' cannot invoke '{func_name}'."}
                        traces.append(ToolCallTrace(
                            tool_name=func_name,
                            query_summary=f"⛔ RBAC Denied: {func_name}",
                            rows_returned=0
                        ))
                        tool_results_text.append(json.dumps(err_res))
                        continue

                    if func_name in HANDLERS:
                        handler = HANDLERS[func_name]
                        try:
                            # Pass db and actor_id for handlers that support it
                            if func_name == "search_hse_knowledge":
                                result_data = handler(**args)
                            else:
                                result_data = handler(db=db, **args)
                        except Exception as exc:
                            result_data = {"error": str(exc)}
                            traces.append(ToolCallTrace(
                                tool_name=func_name,
                                query_summary=f"Failed {func_name}: {exc}",
                                rows_returned=0
                            ))
                            tool_results_text.append(f"Tool {func_name}({args}) failed: {exc}")
                            continue

                        if isinstance(result_data, dict) and "error" not in result_data:
                            last_successful_result = result_data

                        if isinstance(result_data, dict):
                            rows_count = result_data.get("total_count", result_data.get("count", len(result_data.get("rows", []))))
                            if result_data.get("success"):
                                rows_count = 1
                        elif isinstance(result_data, list):
                            rows_count = len(result_data)
                        else:
                            rows_count = 1

                        traces.append(ToolCallTrace(
                            tool_name=func_name,
                            query_summary=f"{func_name} ({rows_count} records / status)",
                            rows_returned=rows_count,
                            args=args if isinstance(args, dict) else None,
                            result=result_data if isinstance(result_data, dict) else None,
                        ))

                        payload = _format_compact_payload(result_data)
                        tool_results_text.append(f"Result for {func_name}({args}): {payload}")
                    else:
                        tool_results_text.append(f"Tool '{func_name}' is not implemented.")

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": "Tool Execution Results:\n" + "\n\n".join(tool_results_text) + "\n\nNow present the final answer clearly in clean Markdown without raw tags or raw SQL."
                })
                continue

            # 2. Embedded SQL recovery
            embedded_sql = _extract_embedded_sql(content)
            if embedded_sql and i < max_loops - 1:
                handler = HANDLERS["run_read_only_query"]
                try:
                    result_data = handler(db=db, sql_query=embedded_sql)
                except Exception as exc:
                    result_data = {"error": str(exc)}

                ret_count = int(result_data.get("returned_count", 0)) if isinstance(result_data, dict) else 0
                traces.append(ToolCallTrace(
                    tool_name="run_read_only_query",
                    query_summary=f"SQL Query ({ret_count} records)",
                    rows_returned=ret_count
                ))

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"Database query result: {json.dumps(result_data, default=str)}\nNow present the final answer to the user clearly in Markdown without raw SQL."
                })
                continue

            # 3. Regular conversational response
            sanitized_content = _sanitize_response_text(content)
            if sanitized_content:
                final_answer = sanitized_content
                SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
                SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})
                return AskResponse(
                    session_id=session_id,
                    answer=final_answer,
                    tool_calls=traces,
                    model_used=last_model_used,
                )
            elif last_successful_result is not None:
                break
            else:
                final_answer = "لم يتم العثور على سجلات مطابقة في قاعدة البيانات. يرجى تقديم سؤال أو معرف أكثر تحديداً."
                SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
                SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})
                return AskResponse(
                    session_id=session_id,
                    answer=final_answer,
                    tool_calls=traces,
                    model_used=last_model_used,
                )

        # Append assistant tool calls
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
        })

        # Process each tool call
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            raw_args = {}
            if tool_call.function.arguments:
                try:
                    raw_args = json.loads(tool_call.function.arguments)
                except Exception:
                    raw_args = {}
            if not isinstance(raw_args, dict):
                raw_args = {}

            args = {k: v for k, v in raw_args.items() if v is not None}

            dedup_key = f"{func_name}:{json.dumps(args, sort_keys=True)}"
            if dedup_key in seen_tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"note": "Already executed — refer to previous tool result."})
                })
                continue
            seen_tool_calls.add(dedup_key)

            # RBAC Check
            is_auth, auth_reason = check_tool_access(canonical_role, func_name)
            if not is_auth:
                err_res = {"error": f"RBAC Access Denied: User role '{canonical_role}' is not authorized to execute tool '{func_name}'."}
                traces.append(ToolCallTrace(
                    tool_name=func_name,
                    query_summary=f"⛔ RBAC Denied: {func_name}",
                    rows_returned=0
                ))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(err_res)
                })
                continue

            if func_name in HANDLERS:
                handler = HANDLERS[func_name]
                try:
                    if func_name == "search_hse_knowledge":
                        result_data = handler(**args)
                    else:
                        result_data = handler(db=db, **args)
                except Exception as exc:
                    result_data = {"error": str(exc)}
                    traces.append(ToolCallTrace(
                        tool_name=func_name,
                        query_summary=f"Failed {func_name}: {exc}",
                        rows_returned=0
                    ))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result_data, default=str)
                    })
                    continue

                if isinstance(result_data, dict) and "error" not in result_data:
                    last_successful_result = result_data

                if isinstance(result_data, dict):
                    rows_count = result_data.get("total_count", result_data.get("count", len(result_data.get("rows", []))))
                    if result_data.get("success"):
                        rows_count = 1
                elif isinstance(result_data, list):
                    rows_count = len(result_data)
                else:
                    rows_count = 1

                traces.append(ToolCallTrace(
                    tool_name=func_name,
                    query_summary=f"{func_name} ({rows_count} records / status)",
                    rows_returned=rows_count,
                    args=args if isinstance(args, dict) else None,
                    result=result_data if isinstance(result_data, dict) else None,
                ))

                payload = _format_compact_payload(result_data)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": payload
                })
            else:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"error": f"Tool '{func_name}' not implemented"})
                })

    # Final synthesis pass if needed
    if last_successful_result is not None:
        data_snapshot = json.dumps(last_successful_result, indent=2, default=str, ensure_ascii=False)
        if len(data_snapshot) > 6000:
            data_snapshot = data_snapshot[:6000] + "\n..."
        try:
            synth_messages = [
                {"role": "system", "content": (
                    "You are an expert Arabic HSE AI report writer for Elsewedy Cables (ESCA HSE Academy). "
                    "You receive tool execution results for Health, Safety & Environment operations. "
                    "Format the response in professional, well-structured Arabic Markdown: "
                    "- For certificate renewal / creation: Present a clean Markdown table with headers 'البيان' and 'التفاصيل'. "
                    "- Always use standard Arabic terminology: 'الأيام المتبقية' (Remaining Days) for validity days — STRICTLY NEVER use 'الأيدي المتبقية' or literal mistranslations. "
                    "- Include: رقم الشهادة (TRN-XXX), اسم الموظف, اسم الدورة التدريبية, تاريخ الانتهاء الجديد, وقت الانتهاء, الحالة (سارية ومعتمدة VALID), الأيام المتبقية. "
                    "- If the certificate is renewed for a standard period (1 or 2 years / 365+ days), provide a positive confirmation that the employee is certified and the competency matrix is updated. Do NOT generate false 48-hour expiration alarms. "
                    "- NEVER output raw JSON, raw SQL, or technical field names."
                )},
                {"role": "user", "content": f"السؤال/الطلب الأصلي: {question}\n\nبيانات التنفيذ:\n{data_snapshot}\n\nقدم الإجابة النهائية بالعربية بأسلوب احترافي مرتب."}
            ]
            synth_res, synth_model = chat_completion(
                messages=synth_messages,
                tools=None,
                local_tools=None,
                tool_choice="none",
                model_mode=model_mode,
            )
            content = (synth_res.choices[0].message.content or "").strip()
            content = _sanitize_response_text(content)
            if content and len(content) > 20:
                final_answer = content
                if synth_model:
                    last_model_used = synth_model
            else:
                final_answer = _format_fallback_table(last_successful_result, question)
        except Exception:
            final_answer = _format_fallback_table(last_successful_result, question)
    else:
        final_answer = "لم يتم العثور على سجلات مطابقة في قاعدة البيانات. يرجى تقديم سؤال أكثر تحديداً."

    final_answer = _sanitize_response_text(final_answer) or "تم تنفيذ العملية بنجاح."
    SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
    SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})

    return AskResponse(
        session_id=session_id,
        answer=final_answer,
        tool_calls=traces,
        model_used=last_model_used,
    )
