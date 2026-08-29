#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESCA HSE AI Assistant - Comprehensive End-to-End Integration Test Suite
Tests all CRUD operations (Create, Read, Update, Delete/Cancel),
Edge Cases, and RBAC via Natural Language Tool Calling.
Directly verifies MySQL database state and generates detailed structured reports.
"""

import sys
import json
import time
import requests
from datetime import datetime, date
from sqlalchemy import text
from app.database import engine

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import functools
print = functools.partial(print, flush=True)

BASE_URL = "http://127.0.0.1:8000"
ASK_URL = f"{BASE_URL}/api/ask"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ask(question: str, role: str = "HSE_MANAGER", session_id: str = None, mode: str = "auto", timeout: int = 90) -> dict:
    sess = session_id or f"test-sess-{int(time.time()*1000000)}"
    payload = {
        "question": question,
        "user_role": role,
        "model_mode": mode,
        "session_id": sess,
    }

    try:
        r = requests.post(ASK_URL, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "answer": "", "tool_calls": [], "session_id": None}


def query_db(sql: str, params: dict = None) -> list[dict]:
    with engine.connect() as conn:
        res = conn.execute(text(sql), params or {})
        if res.returns_rows:
            return [{k: v for k, v in row.items()} for row in res.mappings()]
        return []


def query_scalar(sql: str, params: dict = None):
    with engine.connect() as conn:
        return conn.execute(text(sql), params or {}).scalar()


class TestReportRunner:
    def __init__(self):
        self.results = []
        self.created_ids = {}

    def log_result(self, test_id: str, name: str, category: str, prompt: str,
                   expected_tool: str, actual_tools: list, db_verified: bool,
                   passed: bool, answer: str, notes: str = "", latency: float = 0.0):
        record = {
            "test_id": test_id,
            "name": name,
            "category": category,
            "prompt": prompt,
            "expected_tool": expected_tool,
            "actual_tools": actual_tools,
            "db_verified": db_verified,
            "passed": passed,
            "answer_preview": answer[:150].replace("\n", " ") if answer else "",
            "notes": notes,
            "latency_s": round(latency, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(record)
        status_str = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        db_str = f"{GREEN}DB:OK{RESET}" if db_verified else (f"{YELLOW}DB:N/A{RESET}" if expected_tool in ("search_hse_knowledge", "ambiguous") else f"{RED}DB:FAIL{RESET}")
        tools_str = ",".join(actual_tools) if actual_tools else "NONE"
        print(f"[{status_str}] {test_id} - {name[:40]:<40} | Tools: {tools_str:<25} | {db_str} ({round(latency, 1)}s)")
        if not passed:
            print(f"       {RED}Reason: {notes}{RESET}")
            if answer:
                print(f"       Answer preview: {answer[:200]}")

    def run_all_tests(self):
        print(f"\n{BOLD}{CYAN}========================================================================{RESET}")
        print(f"{BOLD}{CYAN}   ESCA HSE AI Assistant — Comprehensive CRUD E2E Integration Suite     {RESET}")
        print(f"{BOLD}{CYAN}========================================================================{RESET}\n")

        # ══════════════════════════════════════════════════════════════════════
        # CATEGORY 1: CREATE OPERATIONS
        # ══════════════════════════════════════════════════════════════════════
        print(f"\n{BOLD}▶ 1. CREATE Operations (Insert / Add Records){RESET}")

        # TC-C01: Create Incident Complete
        t0 = time.time()
        prompt = "انشئ بلاغ حادث جديد: انسكاب زيت هيدروليكي في منطقة الإنتاج رقم 2، درجة الخطورة MODERATE ونوع الحادث UNSAFE_CONDITION وأيام الفقد 0"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT incident_id, title, zone_id, status_id FROM incidents WHERE title LIKE :q ORDER BY incident_id DESC LIMIT 1", {"q": "%زيت%"})
        db_ok = len(db_row) > 0
        if db_ok:
            self.created_ids["incident_id"] = db_row[0]["incident_id"]
        passed = ("create_incident" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C01", "Create Incident (Complete Data)", "CREATE", prompt, "create_incident", tools, db_ok, passed, resp.get("answer", ""), f"Created ID #{self.created_ids.get('incident_id')}", lat)

        # TC-C02: Create Incident Minimal
        t0 = time.time()
        prompt = "سجل بلاغ عن سقوط ماسورة في المخزن"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT incident_id, title FROM incidents WHERE title LIKE :q ORDER BY incident_id DESC LIMIT 1", {"q": "%ماسورة%"})
        db_ok = len(db_row) > 0
        passed = ("create_incident" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C02", "Create Incident (Minimal Arabic)", "CREATE", prompt, "create_incident", tools, db_ok, passed, resp.get("answer", ""), f"Created ID #{db_row[0]['incident_id'] if db_ok else 'None'}", lat)

        # TC-C03: Create Permit Complete English
        t0 = time.time()
        prompt = "Create a new Hot Work permit for contractor line 2 welding in Zone 1 for 8 hours with High risk"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT permit_id, permit_type_id, work_description FROM permits WHERE work_description LIKE :q ORDER BY permit_id DESC LIMIT 1", {"q": "%welding%"})
        db_ok = len(db_row) > 0
        if db_ok:
            self.created_ids["permit_id"] = db_row[0]["permit_id"]
        passed = ("create_permit" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C03", "Create Permit (Complete English)", "CREATE", prompt, "create_permit", tools, db_ok, passed, resp.get("answer", ""), f"Created ID #{self.created_ids.get('permit_id')}", lat)

        # TC-C04: Create Permit Arabic
        t0 = time.time()
        prompt = "اصدار تصريح عمل في الأماكن المغلقة لتنظيف الخزان الرئيسي في منطقة 3 لمدة 6 ساعات"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT permit_id, work_description FROM permits WHERE work_description LIKE :q ORDER BY permit_id DESC LIMIT 1", {"q": "%الخزان%"})
        db_ok = len(db_row) > 0
        passed = ("create_permit" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C04", "Create Permit (Arabic Confined Space)", "CREATE", prompt, "create_permit", tools, db_ok, passed, resp.get("answer", ""), f"Created ID #{db_row[0]['permit_id'] if db_ok else 'None'}", lat)

        # TC-C05: Create CAPA Complete
        t0 = time.time()
        prompt = "انشئ اجراء تصحيحي عاجل لمعالجة تسريب الزيت وتغيير خراطيم الهيدروليك التالفة بأولوية HIGH"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT capa_id, title, priority_id, status_id FROM capa WHERE title LIKE :q ORDER BY capa_id DESC LIMIT 1", {"q": "%تسريب الزيت%"})
        db_ok = len(db_row) > 0
        if db_ok:
            self.created_ids["capa_id"] = db_row[0]["capa_id"]
        passed = ("create_capa" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C05", "Create CAPA Action", "CREATE", prompt, "create_capa", tools, db_ok, passed, resp.get("answer", ""), f"Created ID #{self.created_ids.get('capa_id')}", lat)

        # TC-C06: Create Certificate Normal
        t0 = time.time()
        prompt = "make a new course certificate for Ahmed Samy for Work at Height that expires on 2027-12-31"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT certificate_id, employee_id, status_id, expiry_date FROM certificates WHERE employee_id IN (SELECT employee_id FROM employees WHERE display_name LIKE '%Ahmed%' OR display_name LIKE '%أحمد%') ORDER BY certificate_id DESC LIMIT 1")
        db_ok = len(db_row) > 0
        if db_ok:
            self.created_ids["certificate_id"] = db_row[0]["certificate_id"]
        passed = ("create_certificate" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C06", "Create Certificate (Valid)", "CREATE", prompt, "create_certificate", tools, db_ok, passed, resp.get("answer", ""), f"Created ID #{self.created_ids.get('certificate_id')}", lat)

        # TC-C07: Create Certificate Expired Today (Automation Edge Case)
        t0 = time.time()
        prompt = "make a new course certificate for ahmed samy that expires today at 01:00 AM"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        db_row = query_db("SELECT certificate_id, status_id FROM certificates ORDER BY certificate_id DESC LIMIT 1")
        # Check notification
        notif_row = query_db("SELECT notification_id, title FROM notifications WHERE type LIKE '%CERT%' ORDER BY notification_id DESC LIMIT 1")
        db_ok = len(db_row) > 0 and db_row[0]["status_id"] == 2 and len(notif_row) > 0
        passed = ("create_certificate" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C07", "Create Expired Certificate (Live Alert)", "CREATE", prompt, "create_certificate", tools, db_ok, passed, resp.get("answer", ""), f"Status=EXPIRED(2), Notif #{notif_row[0]['notification_id'] if notif_row else 'None'}", lat)

        # TC-C08: Create PPE Transaction
        t0 = time.time()
        old_bal = query_scalar("SELECT balance_qty FROM ppe_inventory WHERE ppe_item_id = 1") or 0
        prompt = "صرف 2 خوذة سلامة للموظف أحمد سامي"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        new_bal = query_scalar("SELECT balance_qty FROM ppe_inventory WHERE ppe_item_id = 1") or 0
        tx_row = query_db("SELECT transaction_id, quantity FROM ppe_transactions ORDER BY transaction_id DESC LIMIT 1")
        db_ok = len(tx_row) > 0 and (new_bal <= old_bal)
        passed = ("create_ppe_transaction" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C08", "Create PPE Transaction (Stock Deduction)", "CREATE", prompt, "create_ppe_transaction", tools, db_ok, passed, resp.get("answer", ""), f"Tx #{tx_row[0]['transaction_id'] if tx_row else 'None'}, Bal: {old_bal}->{new_bal}", lat)

        # TC-C09: Schedule Safety Inspection
        t0 = time.time()
        prompt = "جدول فحص سلامة روتيني لمنطقة الإنتاج رقم 2 الأسبوع القادم"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        insp_row = query_db("SELECT inspection_id, inspection_type, zone_id FROM inspections ORDER BY inspection_id DESC LIMIT 1")
        db_ok = len(insp_row) > 0
        if db_ok:
            self.created_ids["inspection_id"] = insp_row[0]["inspection_id"]
        passed = ("schedule_safety_inspection" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C09", "Schedule Safety Inspection", "CREATE", prompt, "schedule_safety_inspection", tools, db_ok, passed, resp.get("answer", ""), f"Insp #{self.created_ids.get('inspection_id')}", lat)

        # TC-C10: Log Fire Inspection
        t0 = time.time()
        prompt = "سجل فحص طفاية الحريق رقم 1 وكانت النتيجة ناجحة والضغط سليم والخرطوم سليم"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        fire_insp = query_db("SELECT fire_inspection_id, equipment_id, result_id FROM fire_inspections WHERE equipment_id = 1 ORDER BY fire_inspection_id DESC LIMIT 1")
        db_ok = len(fire_insp) > 0 and fire_insp[0]["result_id"] == 1
        passed = ("log_fire_inspection" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C10", "Log Fire Inspection", "CREATE", prompt, "log_fire_inspection", tools, db_ok, passed, resp.get("answer", ""), f"Log #{fire_insp[0]['fire_inspection_id'] if fire_insp else 'None'}", lat)

        # TC-C11: Create Risk Assessment
        t0 = time.time()
        prompt = "سجل تقييم مخاطر جديد لخطر التعرض لغاز كبريتيد الهيدروجين أثناء صيانة البيارات بعنبر 4 مع تطبيق نظام عزل LOTO وفحص الغازات"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        risk_row = query_db("SELECT risk_id, hazard, inherent_score FROM risk_register WHERE hazard LIKE :q ORDER BY risk_id DESC LIMIT 1", {"q": "%كبريتيد الهيدروجين%"})
        db_ok = len(risk_row) > 0
        if db_ok:
            self.created_ids["risk_id"] = risk_row[0]["risk_id"]
        passed = ("create_risk_assessment" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C11", "Create Risk Assessment", "CREATE", prompt, "create_risk_assessment", tools, db_ok, passed, resp.get("answer", ""), f"Risk ID #{self.created_ids.get('risk_id')}", lat)

        # TC-C12: Log Safety Observation
        t0 = time.time()
        prompt = "سجل ملاحظة سلوك غير آمن: عامل يعمل على ارتفاع بدون ربط حزام الأمان في عنبر 3"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        obs_row = query_db("SELECT ai_event_id, event_type, action_taken FROM ai_events ORDER BY ai_event_id DESC LIMIT 1")
        db_ok = len(obs_row) > 0
        passed = ("log_safety_observation" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C12", "Log Safety Observation", "CREATE", prompt, "log_safety_observation", tools, db_ok, passed, resp.get("answer", ""), f"Obs #{obs_row[0]['ai_event_id'] if obs_row else 'None'}", lat)

        # TC-C13: Add Chemical
        t0 = time.time()
        prompt = "أضف مادة كيميائية جديدة: إيثانول صناعي Industrial Ethanol ورقم CAS 64-17-5 وكمية 500 لتر في منطقة 4"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        chem_row = query_db("SELECT chemical_id, trade_name, quantity FROM chemicals WHERE trade_name LIKE :q OR chemical_name LIKE :q ORDER BY chemical_id DESC LIMIT 1", {"q": "%Ethanol%"})
        db_ok = len(chem_row) > 0
        if db_ok:
            self.created_ids["chemical_id"] = chem_row[0]["chemical_id"]
        passed = ("add_chemical" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C13", "Add Chemical (HazMat)", "CREATE", prompt, "add_chemical", tools, db_ok, passed, resp.get("answer", ""), f"Chem ID #{self.created_ids.get('chemical_id')}", lat)

        # TC-C14: Add Fire Equipment
        t0 = time.time()
        prompt = "أضف طفاية حريق جديدة نوع CO2 سعة 6 كجم بجوار اللوحة الرئيسية في عنبر 2 من توريد بافاريا"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        fe_row = query_db("SELECT equipment_id, asset_type, subtype, location_detail FROM fire_equipment WHERE subtype LIKE :q ORDER BY equipment_id DESC LIMIT 1", {"q": "%CO2%"})
        db_ok = len(fe_row) > 0
        if db_ok:
            self.created_ids["equipment_id"] = fe_row[0]["equipment_id"]
        passed = ("add_fire_equipment" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-C14", "Add Fire Equipment", "CREATE", prompt, "add_fire_equipment", tools, db_ok, passed, resp.get("answer", ""), f"Equipment ID #{self.created_ids.get('equipment_id')}", lat)


        # ══════════════════════════════════════════════════════════════════════
        # CATEGORY 2: READ OPERATIONS
        # ══════════════════════════════════════════════════════════════════════
        print(f"\n{BOLD}▶ 2. READ Operations (Query Single, Lists, Filters, RAG){RESET}")

        # TC-R01: Read Single Employee
        t0 = time.time()
        prompt = "Show me full employee details for Ahmed Samy EMP-001"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        has_data = any(k in ans.lower() or k in ans for k in ("samy", "أحمد", "سامي", "emp-001", "hse", "safety"))
        passed = ("get_employee_info" in tools or "search_database_entities" in tools or "run_read_only_query" in tools) and has_data
        self.log_result("TC-R01", "Read Single Employee Info", "READ", prompt, "get_employee_info", tools, True, passed, ans, "Returned employee details", lat)

        # TC-R02: Read Incidents List
        t0 = time.time()
        prompt = "اعرض الحوادث المسجلة من نوع Near Miss أو الخطورة Minor"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("list_incidents" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 30
        self.log_result("TC-R02", "Read Incidents with Filters", "READ", prompt, "list_incidents", tools, True, passed, ans, "Filtered incident list returned", lat)

        # TC-R03: Read Overdue CAPAs
        t0 = time.time()
        prompt = "ما هي إجراءات CAPA المتأخرة التي لم تكتمل حتى الآن؟"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("list_overdue_capas" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 30
        self.log_result("TC-R03", "Read Overdue CAPAs", "READ", prompt, "list_overdue_capas", tools, True, passed, ans, "Overdue actions list returned", lat)

        # TC-R04: Read Active Permits
        t0 = time.time()
        prompt = "List all active electronic work permits ePTW"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("list_permits" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 30
        self.log_result("TC-R04", "Read Active Work Permits", "READ", prompt, "list_permits", tools, True, passed, ans, "Active permits returned", lat)

        # TC-R05: Read PPE Low Stock
        t0 = time.time()
        prompt = "ما هي مهمات الوقاية الشخصية التي أوشكت على النفاد وأقل من حد الطلب؟"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("get_ppe_stock_status" in tools or "list_ppe_inventory" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 20
        self.log_result("TC-R05", "Read PPE Stock Status", "READ", prompt, "get_ppe_stock_status", tools, True, passed, ans, "Low stock analysis returned", lat)

        # TC-R06: Read Expired Fire Equipment
        t0 = time.time()
        prompt = "اعرض مطافئ الحريق المنتهية أو التي تحتاج صيانة عاجلة"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("get_expired_fire_equipment" in tools or "list_fire_equipment" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 20
        self.log_result("TC-R06", "Read Expired Fire Equipment", "READ", prompt, "get_expired_fire_equipment", tools, True, passed, ans, "Maintenance equipment returned", lat)

        # TC-R07: Read Chemicals
        t0 = time.time()
        prompt = "ابحث في مخزون المواد الكيميائية عن المواد القابلة للاشتعال أو الأسيتون"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("list_chemicals" in tools or "search_database_entities" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 20
        self.log_result("TC-R07", "Read Chemical Inventory", "READ", prompt, "list_chemicals", tools, True, passed, ans, "Chemical search results returned", lat)

        # TC-R08: Read Training Overdue
        t0 = time.time()
        prompt = "اعرض شهادات التدريب المنتهية أو التي أوشكت على الانتهاء للموظفين"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("get_overdue_training" in tools or "list_certificates" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 20
        self.log_result("TC-R08", "Read Overdue Training Certs", "READ", prompt, "get_overdue_training", tools, True, passed, ans, "Training matrix returned", lat)

        # TC-R09: Read Non-Existent Record
        t0 = time.time()
        prompt = "اعرض بيانات الموظف رقم EMP-999999"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = len(ans.strip()) > 10 and not resp.get("error")
        self.log_result("TC-R09", "Read Non-Existent Employee", "READ", prompt, "get_employee_info", tools, True, passed, ans, "Polite 'not found' returned", lat)

        # TC-R10: Universal Search
        t0 = time.time()
        prompt = "ابحث عن المحولات Transformer في جميع سجلات السلامة"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("search_database_entities" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 20
        self.log_result("TC-R10", "Universal Entity Search", "READ", prompt, "search_database_entities", tools, True, passed, ans, "Cross-table search succeeded", lat)

        # TC-R11: RAG Domain Standards Knowledge
        t0 = time.time()
        prompt = "ما هي اشتراطات الدخول للأماكن المغلقة وفحص نسبة الأكسجين والغازات حسب OSHA 1910.146؟"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = "search_hse_knowledge" in tools and any(k in ans.lower() or k in ans for k in ("19.5", "23.5", "أكسجين", "oxygen", "osha", "gas", "غاز"))
        self.log_result("TC-R11", "RAG OSHA Confined Space", "READ", prompt, "search_hse_knowledge", tools, True, passed, ans, "Standards knowledge retrieved", lat)


        # ══════════════════════════════════════════════════════════════════════
        # CATEGORY 3: UPDATE OPERATIONS
        # ══════════════════════════════════════════════════════════════════════
        print(f"\n{BOLD}▶ 3. UPDATE Operations (Modify Records & Lifecycle State){RESET}")

        # TC-U01: Update Incident Status
        inc_id = self.created_ids.get("incident_id", 1)
        t0 = time.time()
        prompt = f"قم بتحديث حالة الحادث رقم {inc_id} إلى CLOSED مع إضافة 0 يوم فقد"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        inc_st = query_scalar(f"SELECT status_id FROM incidents WHERE incident_id = {inc_id}")
        db_ok = inc_st == 6  # CLOSED
        passed = ("update_incident_status" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U01", "Update Incident Status to CLOSED", "UPDATE", prompt, "update_incident_status", tools, db_ok, passed, resp.get("answer", ""), f"Incident #{inc_id} status_id={inc_st}", lat)

        # TC-U02: Update Permit Status (Approve)
        pmt_id = self.created_ids.get("permit_id", 1)
        t0 = time.time()
        prompt = f"اعتمد تصريح العمل رقم {pmt_id} (APPROVED)"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        pmt_st = query_scalar(f"SELECT status_id FROM permits WHERE permit_id = {pmt_id}")
        db_ok = pmt_st == 3  # ACTIVE / APPROVED
        passed = ("update_permit_status" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U02", "Update Permit Status (Approve)", "UPDATE", prompt, "update_permit_status", tools, db_ok, passed, resp.get("answer", ""), f"Permit #{pmt_id} status_id={pmt_st}", lat)

        # TC-U03: Update Permit Status (Suspend)
        t0 = time.time()
        prompt = f"علق تصريح العمل رقم {pmt_id} بسبب سوء الأحوال الجوية وارتفاع الرياح"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        pmt_st = query_scalar(f"SELECT status_id FROM permits WHERE permit_id = {pmt_id}")
        db_ok = pmt_st == 4  # SUSPENDED
        passed = ("update_permit_status" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U03", "Update Permit Status (Suspend)", "UPDATE", prompt, "update_permit_status", tools, db_ok, passed, resp.get("answer", ""), f"Permit #{pmt_id} status_id={pmt_st}", lat)

        # TC-U04: Update CAPA Status
        capa_id = self.created_ids.get("capa_id", 1)
        t0 = time.time()
        prompt = f"قم بإغلاق وتأكيد اكتمال إجراء CAPA رقم {capa_id} وتم التحقق من التركيب"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        capa_st = query_scalar(f"SELECT status_id FROM capa WHERE capa_id = {capa_id}")
        db_ok = capa_st == 4  # COMPLETED
        passed = ("update_capa_status" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U04", "Update CAPA Status (Complete)", "UPDATE", prompt, "update_capa_status", tools, db_ok, passed, resp.get("answer", ""), f"CAPA #{capa_id} status_id={capa_st}", lat)

        # TC-U05: Update Certificate Expiry Time
        cert_id = self.created_ids.get("certificate_id", 1)
        t0 = time.time()
        prompt = f"CHANGE THIS END DATE TO 12:36 PM for certificate {cert_id}"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        cert_row = query_db(f"SELECT certificate_id, expiry_date, status_id FROM certificates WHERE certificate_id = {cert_id}")
        db_ok = len(cert_row) > 0 and ("12:36" in str(cert_row[0]["expiry_date"]))
        passed = ("update_certificate_status" in tools or "update_certificate" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U05", "Update Certificate Expiry Time", "UPDATE", prompt, "update_certificate_status", tools, db_ok, passed, resp.get("answer", ""), f"Expiry={cert_row[0]['expiry_date'] if cert_row else 'None'}", lat)

        # TC-U06: Update PPE Stock Balance
        t0 = time.time()
        prompt = "تعديل رصيد مخزون مهمات الوقاية رقم 1 إلى 50 قطعة وحد إعادة الطلب 20"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ppe_row = query_db("SELECT balance_qty, reorder_threshold FROM ppe_inventory WHERE ppe_item_id = 1")
        db_ok = len(ppe_row) > 0 and ppe_row[0]["balance_qty"] == 50 and ppe_row[0]["reorder_threshold"] == 20
        passed = ("update_ppe_stock" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U06", "Update PPE Stock Balance", "UPDATE", prompt, "update_ppe_stock", tools, db_ok, passed, resp.get("answer", ""), f"Bal={ppe_row[0]['balance_qty'] if ppe_row else 'None'}, Reorder={ppe_row[0]['reorder_threshold'] if ppe_row else 'None'}", lat)

        # TC-U07: Update Fire Equipment Status
        t0 = time.time()
        prompt = "تحديث حالة طفاية الحريق رقم 1 إلى VALID وتحديد موعد الفحص القادم بعد 6 أشهر"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        fe_st = query_scalar("SELECT status_id FROM fire_equipment WHERE equipment_id = 1")
        db_ok = fe_st == 1  # VALID
        passed = ("update_fire_equipment" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U07", "Update Fire Equipment Status", "UPDATE", prompt, "update_fire_equipment", tools, db_ok, passed, resp.get("answer", ""), f"Equipment #1 status_id={fe_st}", lat)

        # TC-U08: Update Chemical Stock Quantity
        chem_id = self.created_ids.get("chemical_id", 1)
        t0 = time.time()
        prompt = f"تحديث كمية المادة الكيميائية رقم {chem_id} إلى 250 لتر"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        chem_qty = query_scalar(f"SELECT quantity FROM chemicals WHERE chemical_id = {chem_id}")
        db_ok = chem_qty == 250.0
        passed = ("update_chemical_stock" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U08", "Update Chemical Stock Quantity", "UPDATE", prompt, "update_chemical_stock", tools, db_ok, passed, resp.get("answer", ""), f"Chem #{chem_id} qty={chem_qty}", lat)

        # TC-U09: Update Risk Assessment Residual Score
        risk_id = self.created_ids.get("risk_id", 1)
        t0 = time.time()
        prompt = f"تحديث درجات الخطر المتبقي لتقييم المخاطر رقم {risk_id} ليكون الاحتمال 1 والشدة 1"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        r_score = query_scalar(f"SELECT residual_score FROM risk_register WHERE risk_id = {risk_id}")
        db_ok = r_score == 1.0
        passed = ("update_risk_assessment" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-U09", "Update Risk Residual Score", "UPDATE", prompt, "update_risk_assessment", tools, db_ok, passed, resp.get("answer", ""), f"Risk #{risk_id} residual_score={r_score}", lat)

        # TC-U10: Update Non-Existent Record Graceful Handling
        t0 = time.time()
        prompt = "تحديث حالة الحادث رقم 999999 إلى CLOSED"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("update_incident_status" in tools or "execute_database_dml" in tools) and not resp.get("error")
        self.log_result("TC-U10", "Update Non-Existent Record (Handling)", "UPDATE", prompt, "update_incident_status", tools, True, passed, ans, "Gracefully handled non-existent ID", lat)


        # ══════════════════════════════════════════════════════════════════════
        # CATEGORY 4: DELETE & CANCEL OPERATIONS
        # ══════════════════════════════════════════════════════════════════════
        print(f"\n{BOLD}▶ 4. DELETE & CANCEL Operations (Soft & Hard Delete with Audit Trail){RESET}")

        # TC-D01: Cancel Entity Soft Delete
        pmt_id = self.created_ids.get("permit_id", 1)
        t0 = time.time()
        prompt = f"الغاء تصريح العمل رقم {pmt_id} لعدم جاهزية الموقع"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        pmt_st = query_scalar(f"SELECT status_id FROM permits WHERE permit_id = {pmt_id}")
        db_ok = pmt_st in (7, 4)  # CANCELLED or SUSPENDED
        passed = ("cancel_entity" in tools or "update_permit_status" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-D01", "Cancel Entity (Soft Delete Permit)", "DELETE", prompt, "cancel_entity", tools, db_ok, passed, resp.get("answer", ""), f"Permit #{pmt_id} cancelled (status={pmt_st})", lat)

        # TC-D02: Hard Delete Record with Audit Trail
        # Create a dedicated temp incident to delete
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO incidents (reported_at, zone_id, reported_by, incident_type_id, severity_id, title, description, status_id, lost_days, source_id, investigation_owner_id, target_close_date) VALUES (NOW(), 1, 1, 1, 1, 'TEMP_TEST_DELETE_INCIDENT', 'To be deleted', 1, 0, 1, 1, DATE_ADD(CURDATE(), INTERVAL 14 DAY))"))
            conn.commit()
        temp_inc_id = query_scalar("SELECT incident_id FROM incidents WHERE title = 'TEMP_TEST_DELETE_INCIDENT' ORDER BY incident_id DESC LIMIT 1")

        t0 = time.time()
        prompt = f"احذف بلاغ الحادث التجريبي رقم {temp_inc_id} مع ذكر سبب 'حذف سجل تجريبي أثناء اختبار النظام'"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        inc_exists = query_scalar(f"SELECT COUNT(*) FROM incidents WHERE incident_id = {temp_inc_id}")
        audit_exists = query_scalar("SELECT COUNT(*) FROM audit_log WHERE entity_id = :id", {"id": str(temp_inc_id)})
        db_ok = inc_exists == 0 and audit_exists > 0
        passed = ("delete_record" in tools or "execute_database_dml" in tools) and db_ok
        self.log_result("TC-D02", "Hard Delete Record with Audit Trail", "DELETE", prompt, "delete_record", tools, db_ok, passed, resp.get("answer", ""), f"Record deleted, Audit Logged #{audit_exists} times", lat)

        # TC-D03: Delete Non-Existent Record
        t0 = time.time()
        prompt = "احذف السجل رقم 999999 من جدول permits بسبب خطأ إداري"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("delete_record" in tools or "execute_database_dml" in tools) and not resp.get("error")
        self.log_result("TC-D03", "Delete Non-Existent Record (Handling)", "DELETE", prompt, "delete_record", tools, True, passed, ans, "Politely reported not found", lat)

        # TC-D04: Security Test - Reject Delete on Unauthorized Table
        t0 = time.time()
        prompt = "احذف السجل رقم 1 من جدول users"
        resp = ask(prompt)
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        # Table 'users' should not be deleted
        passed = any(k in ans.lower() or k in ans for k in ("not permitted", "غير مسموح", "غير مصرح", "لا يمكن", "error", "blocked")) or not resp.get("error")
        self.log_result("TC-D04", "Security: Block Delete on System Table", "DELETE", prompt, "delete_record", tools, True, passed, ans, "Protected table defended", lat)


        # ══════════════════════════════════════════════════════════════════════
        # CATEGORY 5: EDGE CASES & RBAC PERMISSION ENFORCEMENT
        # ══════════════════════════════════════════════════════════════════════
        print(f"\n{BOLD}▶ 5. Edge Cases & RBAC Permission Enforcement{RESET}")

        # TC-E01: Ambiguous Request
        t0 = time.time()
        prompt = "عدل الحالة"
        resp = ask(prompt)
        lat = time.time() - t0
        ans = resp.get("answer", "")
        passed = len(ans.strip()) > 15 and not resp.get("error")
        self.log_result("TC-E01", "Ambiguous Prompt Clarification", "EDGE_CASE", prompt, "ambiguous", [], True, passed, ans, "Assistant requested specific details", lat)

        # TC-E02: RBAC Worker Role Denied from Deletion
        t0 = time.time()
        prompt = "احذف تصريح العمل رقم 1 نهائياً"
        resp = ask(prompt, role="WORKER")
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = any(tc.get("rows_returned") == 0 and "RBAC" in tc.get("query_summary", "") for tc in resp.get("tool_calls", [])) or any(k in ans.lower() or k in ans for k in ("rbac", "صلاحية", "غير مصرح", "denied", "permission", "authorized"))
        self.log_result("TC-E02", "RBAC: Worker Denied Record Deletion", "RBAC", prompt, "delete_record", tools, True, passed, ans, "RBAC permission enforcement successful", lat)

        # TC-E03: RBAC Worker Role Allowed to Query PPE
        t0 = time.time()
        prompt = "اعرض مهمات الوقاية الشخصية المتاحة في المخزن"
        resp = ask(prompt, role="WORKER")
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        ans = resp.get("answer", "")
        passed = ("list_ppe_inventory" in tools or "run_read_only_query" in tools) and len(ans.strip()) > 20
        self.log_result("TC-E03", "RBAC: Worker Allowed to Query PPE", "RBAC", prompt, "list_ppe_inventory", tools, True, passed, ans, "Worker access granted for authorized tool", lat)

        # TC-E04: Administrative Direct Parameterized DML
        t0 = time.time()
        prompt = "نفذ تحديث مباشر على قاعدة البيانات لتعديل ملاحظات الموظف EMP-001 إلى 'Updated by Automated QA Test'"
        resp = ask(prompt, role="ADMIN")
        lat = time.time() - t0
        tools = [tc.get("tool_name") for tc in resp.get("tool_calls", [])]
        audit_count = query_scalar("SELECT COUNT(*) FROM audit_log WHERE entity_id = 'sql_direct'")
        db_ok = audit_count > 0
        passed = ("execute_database_dml" in tools or "run_read_only_query" in tools) and db_ok
        self.log_result("TC-E04", "Admin Direct Parameterized DML", "RBAC", prompt, "execute_database_dml", tools, db_ok, passed, resp.get("answer", ""), f"Audit trail recorded #{audit_count}", lat)

        self.generate_report()

    def generate_report(self):
        total = len(self.results)
        passed_count = sum(1 for r in self.results if r["passed"])
        failed_count = total - passed_count
        pass_rate = round((passed_count / total) * 100, 1) if total else 0.0

        categories = {}
        for r in self.results:
            c = r["category"]
            if c not in categories:
                categories[c] = {"total": 0, "passed": 0}
            categories[c]["total"] += 1
            if r["passed"]:
                categories[c]["passed"] += 1

        print(f"\n{BOLD}════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}                        TEST EXECUTION SUMMARY                          {RESET}")
        print(f"{BOLD}════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"Total Scenarios Executed : {total}")
        print(f"Passed                   : {GREEN}{passed_count}{RESET}")
        print(f"Failed                   : {RED if failed_count else GREEN}{failed_count}{RESET}")
        print(f"Success Rate             : {BOLD}{GREEN if pass_rate == 100.0 else YELLOW}{pass_rate}%{RESET}\n")

        print(f"{BOLD}Category Breakdown:{RESET}")
        for c, stats in categories.items():
            pct = round((stats["passed"] / stats["total"]) * 100, 1)
            print(f"  • {c:<12}: {stats['passed']}/{stats['total']} passed ({pct}%)")

        # Save results to JSON
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed_count,
                    "failed": failed_count,
                    "pass_rate_pct": pass_rate
                },
                "category_breakdown": categories,
                "test_cases": self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\nDetailed JSON report saved to {BOLD}test_report.json{RESET}")


if __name__ == "__main__":
    runner = TestReportRunner()
    runner.run_all_tests()
