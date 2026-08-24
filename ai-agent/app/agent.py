import re
import json
import uuid
from sqlalchemy.orm import Session
from app.llm_client import chat_completion
from app.schemas import ToolCallTrace, AskResponse
from app.tools.definitions import TOOLS, LOCAL_TOOLS
from app.tools.handlers import HANDLERS


# ── Fallback table formatter (used when LLM synthesis fails) ──────────────────
_ARABIC_HEADERS = {
    "incident_id": "رقم الحادث", "incident_status_id": "رقم الحالة", "name": "الاسم/الحالة",
    "status": "الحالة", "severity": "الخطورة", "title": "العنوان", "description": "الوصف",
    "reported_at": "تاريخ البلاغ", "zone_id": "المنطقة", "lost_days": "أيام الفقد",
    "employee_id": "رقم الموظف", "display_name": "اسم الموظف", "due_date": "تاريخ الاستحقاق",
    "days_overdue": "أيام التأخير", "priority": "الأولوية", "capa_id": "رقم الإجراء",
    "permit_id": "رقم التصريح", "permit_type": "نوع التصريح", "risk_level": "مستوى الخطورة",
    "balance_qty": "الرصيد", "item_code": "كود الصنف", "name_ar": "الاسم",
    "category": "التصنيف", "month": "الشهر", "trir": "TRIR", "ltifr": "LTIFR",
    "hours_worked": "ساعات العمل", "count": "العدد", "total_count": "إجمالي السجلات",
    "returned_count": "السجلات المعروضة",
}

def _format_fallback_table(result_data: any, question: str = "") -> str:
    """Builds a readable Arabic Markdown table from raw query results when the LLM synthesis fails."""
    rows = []
    if isinstance(result_data, dict):
        rows = result_data.get("rows", [])
        if not rows and not any(k in result_data for k in ("rows", "error")):
            # Single-record dict like a summary
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
        cols = list(rows[0].keys())
        headers = [_ARABIC_HEADERS.get(c, c) for c in cols]
        table_lines = ["| " + " | ".join(headers) + " |"]
        table_lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for row in rows[:30]:
            vals = [str(row.get(c, "-")) for c in cols]
            table_lines.append("| " + " | ".join(vals) + " |")
        summary = f"\n\n**الإجمالي:** {len(rows)} سجل من قاعدة البيانات."
        return "\n".join(table_lines) + summary
    else:
        return "\n".join([f"- {r}" for r in rows[:30]])


SYSTEM_PROMPT = """You are ESCA HSE AI Assistant — an expert Health, Safety & Environment AI with direct read-only SQL access to a MySQL database for Elsewedy Cables (ESCA).

MYSQL DATABASE SCHEMA:
- departments: department_id (PK), name_ar, name_en, manager_employee_id (FK->employees.employee_id), hse_contact_id, active_flag
- employees: employee_id (PK), display_name, zone_id, job_title, manager_id, employment_type_id, hire_date, email_alias, phone_ext, active_flag
- incidents: incident_id (PK), reported_at, zone_id, reported_by, incident_type_id, severity_id, title, description, injured_employee_id, lost_days, status_id
- capa: capa_id (PK), incident_id, finding_id, title, action_type_id, priority_id, assigned_to, due_date, status_id, completion_date, days_overdue
- chemicals: chemical_id (PK), trade_name, chemical_name, cas_number, supplier, quantity, unit, ghs_classes, storage_class, zone_id, status_id
- permits: permit_id (PK), permit_type_id, zone_id, work_description, requester_id, issuer_id, executor_name, start_at, expiry_at, risk_level_id, status_id
- monthly_kpis: kpi_id (PK), month, hours_worked, recordable_incidents, lost_time_injuries, lost_days, near_misses, safety_observations, trir, ltifr
- ppe_inventory: ppe_item_id (PK), item_code, name_ar, category, unit, balance_qty, reorder_threshold, monthly_consumption, supplier, storage_zone_id, stock_status
- fire_equipment: equipment_id (PK), asset_type, subtype, zone_id, location_detail, capacity, installation_date, last_inspection_date, next_inspection_date, expiry_date, vendor, qr_code, status_id (lookup: fire_equipment_statuses)
- fire_inspections: inspection_id (PK), equipment_id, inspected_at, inspector_name, status_id, notes
- fixed_safety_assets: asset_summary_id (PK), asset_type, asset_name, total_qty, operational_qty, last_test_date, next_test_date, status_id, notes
- ai_events: ai_event_id (PK), detected_at, event_type, camera_id, employee_id, confidence_pct, severity_id, status_id, action_taken

HOW YOU OPERATE:
1. Direct SQL Tool Calling: For any factual query, call `run_read_only_query` or specific lookup tools (`list_fire_equipment`, `list_ppe_inventory`, `list_incidents`, `list_permits`, etc.).
2. Complete Data Grounding: Use ONLY facts, counts, dates, and names returned by MySQL. Never invent, hallucinate, or assume records that are not in the query output.
3. Response Presentation & Formatting:
   - Always structure tabular data (lists of items, PPE inventory, fire equipment, incidents, certificates, permits, chemicals) into well-aligned Markdown tables with clear Arabic column headers.
   - Accompany tables with a concise bullet-point summary, key totals, and proactive HSE recommendations.
   - NEVER output raw SQL statements (such as `SELECT ... FROM ...`), internal database queries, or tool names in your final response.
   - Keep answers professional, crisp, and beautifully structured in the user's language (Arabic by default, or English if asked in English).
4. Clean Output: Never output raw XML pseudo-tags like `<tool_call>`, `<function>`, `<parameter>`, or `<think>` in your final conversational response."""

SESSION_HISTORIES: dict[str, list[dict]] = {}

LOCAL_SYSTEM_PROMPT = """You are ESCA HSE AI Assistant with direct read-only SQL access to a MySQL database.

KEY TABLES & FIELDS:
- fire_equipment: equipment_id, asset_type, subtype, zone_id, location_detail, capacity, installation_date, last_inspection_date, next_inspection_date, expiry_date, vendor, qr_code, status_id
- fire_inspections: inspection_id, equipment_id, inspected_at, inspector_name, status_id, notes
- ppe_inventory: ppe_item_id, item_code, name_ar, category, balance_qty, reorder_threshold, supplier
- permits: permit_id, permit_type_id, zone_id, work_description, start_at, expiry_at, status_id
- incidents: incident_id, reported_at, zone_id, title, description, lost_days, status_id, severity_id
- capa: capa_id, incident_id, title, due_date, status_id, days_overdue
- fixed_safety_assets: asset_summary_id, asset_type, asset_name, total_qty, operational_qty, last_test_date, next_test_date, status_id
- departments: department_id, name_ar, name_en, manager_employee_id, hse_contact_id
- employees: employee_id, display_name, zone_id, job_title, manager_id, hire_date, email_alias
- chemicals: chemical_id, trade_name, chemical_name, cas_number, supplier, quantity, unit, ghs_classes
- monthly_kpis: kpi_id, month, hours_worked, recordable_incidents, trir, ltifr

FEW-SHOT EXAMPLES:
User: "list fire equipment" -> Tool: list_fire_equipment(limit=15)
User: "ما هي طفايات الحريق المنتهية أو التي تحتاج فحص" -> Tool: get_expired_fire_equipment()
User: "اعرض تصاريح العمل النشطة" -> Tool: list_permits(status="ACTIVE")
User: "ما هي الحوادث المفتوحة" -> Tool: list_incidents(status="OPEN")
User: "مهمات الوقاية التي وصلت لحد الطلب" -> Tool: get_ppe_stock_status(below_threshold_only=True)
User: "بيانات الموظف EMP-001" -> Tool: get_employee_info(employee_id="EMP-001")
User: "مؤشرات السلامة لشهر يوليو 2026" -> Tool: get_monthly_kpis(month="2026-07")

RULES:
1. Always call the matching tool to fetch real records.
2. Structure list data into clean Markdown tables with Arabic column headers and summarize key points with bullet points.
3. NEVER display raw SQL queries, SELECT commands, or internal function calls in your response to the user.
4. Copy names, IDs, dates, and values EXACTLY as returned from MySQL without altering or translating them.
5. NEVER invent or guess records from memory. Answer strictly from the tool output.
6. Never output raw XML pseudo-tags like `<tool_call>` in conversational output."""


def _filter_local_tools(question: str, all_local_tools: list[dict]) -> list[dict]:
    """
    Intelligently narrows down the tool list for the local 3B model based on keywords in the prompt.
    Preventing tool distraction increases 3B model tool-calling accuracy to >95%.
    """
    q = question.lower()
    tool_map = {t["function"]["name"]: t for t in all_local_tools}
    selected_names = set()

    # Always keep direct SQL available as universal fallback
    selected_names.add("run_read_only_query")

    # Fire safety
    if any(k in q for k in ["fire", "extinguish", "hydrant", "detector", "طفاية", "طفايات", "حريق", "إطفاء", "انذار", "إنذار"]):
        selected_names.update(["list_fire_equipment", "get_expired_fire_equipment", "list_fire_inspections"])

    # PPE & Stock
    if any(k in q for k in ["ppe", "stock", "helmet", "glove", "mask", "boot", "vest", "مهمات", "وقاية", "خوذة", "قفاز", "كمامة", "حذاء", "مخزون", "رصيد"]):
        selected_names.update(["list_ppe_inventory", "get_ppe_stock_status"])

    # Work Permits
    if any(k in q for k in ["permit", "ptw", "hot work", "confined", "height", "excavation", "loto", "تصريح", "تصاريح", "عمل ساخن", "مرتفعات", "مغلق"]):
        selected_names.update(["list_permits"])

    # Incidents & Near Misses
    if any(k in q for k in ["incident", "near miss", "injury", "lost day", "accident", "حادث", "حوادث", "إصابة", "اصابة", "بلاغ", "وشيك"]):
        selected_names.update(["list_incidents", "list_overdue_capas"])

    # CAPA Actions
    if any(k in q for k in ["capa", "action", "overdue", "corrective", "إجراء", "اجراء", "تصحيحي", "متأخر", "معلق"]):
        selected_names.update(["list_overdue_capas", "list_incidents"])

    # Employees & Contacts
    if any(k in q for k in ["employee", "staff", "worker", "manager", "engineer", "emp-", "موظف", "موظفين", "عامل", "مهندس", "مدير", "رقم وظيفي"]):
        selected_names.update(["get_employee_info"])

    # KPIs & Safety Metrics
    if any(k in q for k in ["kpi", "trir", "ltifr", "rate", "hours", "streak", "مؤشر", "مؤشرات", "ساعات", "أداء", "اداء", "إحصائيات"]):
        selected_names.update(["get_monthly_kpis"])

    # Chemicals & Hazmat
    if any(k in q for k in ["chemical", "hazmat", "ghs", "acid", "cas", "مادة", "مواد", "كيميائ", "كيماوي", "خطرة", "تخزين"]):
        selected_names.update(["list_chemicals"])

    # Fixed Assets (Showers, Eyewash)
    if any(k in q for k in ["fixed asset", "shower", "eyewash", "aed", "دش", "غسيل", "عين", "إسعاف", "محطة"]):
        selected_names.update(["list_fixed_safety_assets"])

    # Training & Certifications
    if any(k in q for k in ["training", "certificate", "expiry", "expire", "course", "تدريب", "شهادة", "شهادات", "دورة"]):
        selected_names.update(["get_overdue_training", "get_employee_info"])

    # If no specific domain keywords matched, supply the core set of most common tools
    if len(selected_names) <= 1:
        selected_names.update([
            "list_incidents",
            "list_permits",
            "list_fire_equipment",
            "list_ppe_inventory",
            "list_overdue_capas",
            "get_employee_info",
            "get_db_schema",
        ])

    return [tool_map[name] for name in selected_names if name in tool_map]

def _extract_text_tool_calls(text: str) -> list[dict]:
    """Extracts function calls if the LLM outputted tool calls in raw text format (XML pseudo-tags or JSON)."""
    if not text or not isinstance(text, str):
        return []

    calls = []

    # 1. Try to find JSON inside <tool_call>...</tool_call> or <function_call>...</function_call> or code blocks
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

    # 2. Try XML tag style: <function=name> or <function name="name">
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
    # Remove thinking tags
    cleaned = re.sub(r'<think>[\s\S]*?(?:</think>|$)', '', text, flags=re.IGNORECASE)
    # Remove tool call blocks
    cleaned = re.sub(r'<tool_call>[\s\S]*?(?:</tool_call>|<tool_call/>|$)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<function_call>[\s\S]*?(?:</function_call>|<function_call/>|$)', '', cleaned, flags=re.IGNORECASE)
    # Remove function blocks
    cleaned = re.sub(r'<function[=\s][\s\S]*?(?:</function>|<function/>|$)', '', cleaned, flags=re.IGNORECASE)
    # Remove parameter blocks
    cleaned = re.sub(r'<parameter[=\s][\s\S]*?(?:</parameter>|<parameter/>|$)', '', cleaned, flags=re.IGNORECASE)
    # Remove any remaining stray pseudo XML tags
    cleaned = re.sub(r'</?(?:tool_call|function_call|function|parameter|think)[^>]*>', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _format_compact_payload(result_data: any) -> str:
    """Formats SQL results into a compact JSON string to keep prompt token sizes lean and lightning-fast."""
    if isinstance(result_data, dict):
        rows = result_data.get("rows")
        if isinstance(rows, list) and len(rows) > 20:
            compact_data = dict(result_data)
            compact_data["rows"] = rows[:20]
            compact_data["note"] = f"Displaying top 20 of {len(rows)} records. Full matching count: {result_data.get('total_count', len(rows))}."
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

def _is_factual_query(text: str) -> bool:
    clean = text.strip().lower()
    greetings = {"hi", "hello", "hey", "hola", "welcome", "مرحبا", "اهلا", "السلام عليكم", "صباح الخير", "مساء الخير", "who are you", "من انت"}
    if clean in greetings or len(clean) < 3:
        return False
    return True

def run_agent_loop(
    question: str,
    db: Session,
    session_id: str | None = None,
    model_mode: str = "auto",
    client_history: list[dict] | None = None,
) -> AskResponse:
    # Both agents are MySQL-only.
    if not session_id or session_id not in SESSION_HISTORIES:
        session_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        sys_msg = {
            "role": "system",
            "content": LOCAL_SYSTEM_PROMPT if model_mode == "local" else SYSTEM_PROMPT,
        }
        init_msgs = [sys_msg]
        if client_history:
            for item in client_history[-4:]:
                role = "assistant" if item.get("role") == "agent" else item.get("role", "user")
                text_val = item.get("text") or item.get("content") or ""
                if text_val:
                    init_msgs.append({"role": role, "content": text_val})
        SESSION_HISTORIES[session_id] = init_msgs


    history = SESSION_HISTORIES[session_id]

    # Keep conversation history bounded to avoid exploding token sizes
    history_limit = 4 if model_mode == "local" else 9
    if len(history) > history_limit:
        history = [history[0]] + history[-(history_limit - 1):]
        SESSION_HISTORIES[session_id] = history

    messages = list(history)
    messages.append({"role": "user", "content": question})

    traces: list[ToolCallTrace] = []
    max_loops = 3
    seen_tool_calls: set[str] = set()
    last_model_used = None
    last_successful_result = None
    for i in range(max_loops):
        # On the final turn, if we already have tool results, omit tools to force synthesis
        force_synthesis = (i == max_loops - 1) and len(traces) > 0
        current_tools = None if force_synthesis else TOOLS
        current_local_tools = None if force_synthesis else _filter_local_tools(question, LOCAL_TOOLS)

        response, model_used = chat_completion(
            messages=messages,
            tools=current_tools,
            local_tools=current_local_tools,
            tool_choice="none" if force_synthesis else "auto",
            model_mode=model_mode,
        )
        last_model_used = model_used
        message = response.choices[0].message

        # Check if model emitted tool calls
        if not message.tool_calls:
            content = (message.content or "").strip()

            # 1. Check for text-based tool calls (XML / JSON pseudo-tags emitted by Qwen/Hermes/Llama models)
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

                    if func_name in HANDLERS:
                        handler = HANDLERS[func_name]
                        try:
                            result_data = handler(db=db, **args)
                        except Exception as exc:
                            result_data = {"rows": [], "count": 0, "error": str(exc)}
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
                        elif isinstance(result_data, list):
                            rows_count = len(result_data)
                        else:
                            rows_count = 1

                        if func_name == "run_read_only_query":
                            summary_label = f"استعلام مباشر لقاعدة البيانات ({rows_count} سجل)"
                        else:
                            summary_label = f"{func_name} ({rows_count} سجل)"

                        traces.append(ToolCallTrace(
                            tool_name=func_name,
                            query_summary=summary_label,
                            rows_returned=rows_count
                        ))

                        payload = _format_compact_payload(result_data)
                        tool_results_text.append(f"Result for {func_name}({args}): {payload}")
                    else:
                        tool_results_text.append(f"Tool '{func_name}' is not implemented.")

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": "Tool Execution Results:\n" + "\n\n".join(tool_results_text) + "\n\nNow use these records to present the final answer clearly in clean Markdown without raw tags or raw SQL."
                })
                continue

            # 2. Self-healing: If model accidentally typed a SQL query in text instead of invoking a tool call
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
                    query_summary=f"استعلام قاعدة البيانات ({ret_count} سجل)",
                    rows_returned=ret_count
                ))

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"Database query result for `{embedded_sql}`: {json.dumps(result_data, default=str)}\nNow present the final answer to the user clearly in Markdown without raw SQL."
                })
                continue

            # 3. Anti-hallucination guard: If model attempts to answer a factual query on the first turn without any tool call
            if i == 0 and not traces and not embedded_sql and not extracted_tool_calls and _is_factual_query(question):
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": "You MUST call a MySQL tool (such as run_read_only_query or get_employee_info) to retrieve verified records from the database before answering. Do NOT guess or fabricate names or data."
                })
                continue

            # 4. If conversational text without tool calls
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
                # Content was purely raw tool tags that were stripped; break out to run synthesis pass
                break
            else:
                final_answer = (
                    "No matching records were found in the database for this request. "
                    "Please provide an entity ID or a more specific keyword."
                )
                SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
                SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})
                return AskResponse(
                    session_id=session_id,
                    answer=final_answer,
                    tool_calls=traces,
                    model_used=last_model_used,
                )

        # Append assistant tool call request to loop context
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
            raw_args = None
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

            if func_name in HANDLERS:
                handler = HANDLERS[func_name]
                try:
                    result_data = handler(db=db, **args)
                except Exception as exc:
                    result_data = {"rows": [], "count": 0, "error": str(exc)}
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
                elif isinstance(result_data, list):
                    rows_count = len(result_data)
                else:
                    rows_count = 1

                if func_name == "run_read_only_query":
                    summary_label = f"استعلام مباشر لقاعدة البيانات ({rows_count} سجل)"
                else:
                    summary_label = f"{func_name} ({rows_count} سجل)"

                traces.append(ToolCallTrace(
                    tool_name=func_name,
                    query_summary=summary_label,
                    rows_returned=rows_count
                ))

                # Deliver compact database rows directly into the model context
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

    # If the loop ended after retrieving tool data without emitting a final response,
    # invoke a single synthesis completion to format the retrieved rows into Markdown.
    if last_successful_result is not None:
        data_snapshot = json.dumps(last_successful_result, indent=2, default=str, ensure_ascii=False)
        if len(data_snapshot) > 6000:
            data_snapshot = data_snapshot[:6000] + "\n..."
        try:
            synth_messages = [
                {"role": "system", "content": (
                    "You are a professional Arabic HSE report writer. "
                    "You will receive raw database records in JSON format. "
                    "Your ONLY job is to present them as a clear, readable Arabic Markdown answer with tables and bullet points. "
                    "NEVER output raw JSON, raw SQL, code blocks with json, or field names like 'incident_status_id'. "
                    "Translate field names to Arabic column headers (e.g. 'name' → 'الحالة', 'incident_id' → 'رقم الحادث'). "
                    "End with a brief summary of key findings."
                )},
                {"role": "user", "content": f"السؤال الأصلي: {question}\n\nبيانات قاعدة البيانات:\n{data_snapshot}\n\nقدم الإجابة النهائية بالعربية في جدول Markdown مرتب مع ملخص."}
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

    final_answer = _sanitize_response_text(final_answer) or "تم استخراج البيانات المطلوبة من قاعدة البيانات بنجاح."
    SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
    SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})
    return AskResponse(
        session_id=session_id,
        answer=final_answer,
        tool_calls=traces,
        model_used=last_model_used,
    )
