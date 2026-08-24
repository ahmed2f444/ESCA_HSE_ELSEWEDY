import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from app.database import SessionLocal
from app.agent import run_agent_loop
from sqlalchemy import text

PROMPTS = [
    {
        "id": "1_employees_full",
        "prompt": "List all 10 employees with their display names, job titles, and hire dates.",
        "sql": "SELECT employee_id, display_name, job_title, hire_date FROM employees ORDER BY employee_id",
        "match_keys": ["محمود عبد الله", "هبة فؤاد", "أحمد سامي", "كريم رشاد", "محمد عادل", "سارة حسن", "عمر خالد", "نور أحمد", "ياسر محمود", "دينا مصطفى"]
    },
    {
        "id": "2_departments_managers",
        "prompt": "List all 10 departments and the names of their managers.",
        "sql": """
            SELECT d.department_id, d.name_en, d.name_ar, e.display_name AS manager_name
            FROM departments d
            LEFT JOIN employees e ON d.manager_employee_id = e.employee_id
            ORDER BY d.department_id
        """,
        "match_keys": ["Production Sector A", "Production Sector B", "Maintenance", "Warehousing & Logistics", "Quality", "Administration", "Power & Utilities", "Dispatch", "Chemical Management", "Services"]
    },
    {
        "id": "3_chemicals_full",
        "prompt": "List all 10 chemicals in our inventory with their trade names, CAS numbers, and quantities.",
        "sql": "SELECT chemical_id, trade_name, chemical_name, cas_number, quantity, unit FROM chemicals ORDER BY chemical_id",
        "match_keys": ["DURACLEAN 200", "WELD-ANTI SP", "CUTSAFE 46", "SOLV-IPA", "PAINT THINNER", "SODIUM HYPOCHLORITE", "OXYGEN", "ACETYLENE", "DEGREASER X", "EPOXY RESIN A"]
    },
    {
        "id": "4_incidents_severity",
        "prompt": "What are all the recorded HSE incidents and their severity levels?",
        "sql": """
            SELECT i.incident_id, i.title, s.name AS severity, st.name AS status
            FROM incidents i
            JOIN incident_severities s ON i.severity_id = s.incident_severity_id
            JOIN incident_statuses st ON i.status_id = st.incident_status_id
            ORDER BY i.incident_id
        """,
        "match_keys": ["Near Miss - Forklift Near Collision", "Minor Chemical Splash during Tank Wash", "Steam Pipe Leak in Zone 4", "Slips and Trips on Oily Floor"]
    },
    {
        "id": "5_arabic_query",
        "prompt": "ما هي المواد الكيميائية المسجلة في النظام وما هي درجات خطورتها؟",
        "sql": "SELECT chemical_id, trade_name, ghs_classes FROM chemicals ORDER BY chemical_id",
        "match_keys": ["DURACLEAN 200", "SOLV-IPA", "OXYGEN", "ACETYLENE", "EPOXY RESIN A"]
    }
]

def run_suite():
    db = SessionLocal()
    results = []
    output_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "validation_results.json"))

    print("=" * 80, flush=True)
    print("STARTING EXTENSIVE COMPARATIVE VALIDATION SUITE", flush=True)
    print("=" * 80, flush=True)

    for i, item in enumerate(PROMPTS, 1):
        print(f"\n[{i}/{len(PROMPTS)}] RUNNING TEST: {item['id']}", flush=True)
        print(f"Prompt: \"{item['prompt']}\"", flush=True)
        
        # 1. Ground Truth from MySQL
        gt_rows = [dict(r) for r in db.execute(text(item["sql"])).mappings().all()]
        print(f"[MySQL] Direct query returned {len(gt_rows)} ground truth rows.", flush=True)

        # 2. Groq Agent
        print("  -> Testing Groq Agent...", flush=True)
        t0 = time.time()
        try:
            groq_res = run_agent_loop(question=item["prompt"], db=db, model_mode="groq")
            groq_dur = round(time.time() - t0, 2)
            groq_text = groq_res.answer
            groq_tools = [t.tool_name for t in groq_res.tool_calls]
            groq_missing = [k for k in item["match_keys"] if k.lower() not in groq_text.lower()]
            print(f"     [Groq] Done in {groq_dur}s | Tools: {groq_tools} | Missing: {len(groq_missing)}/{len(item['match_keys'])}", flush=True)
        except Exception as exc:
            groq_dur = round(time.time() - t0, 2)
            groq_text = f"ERROR: {exc}"
            groq_tools = []
            groq_missing = item["match_keys"]
            print(f"     [Groq] FAILED ({exc})", flush=True)

        # 3. Local Ollama Agent
        print("  -> Testing Local Ollama Agent...", flush=True)
        t0 = time.time()
        try:
            local_res = run_agent_loop(question=item["prompt"], db=db, model_mode="local")
            local_dur = round(time.time() - t0, 2)
            local_text = local_res.answer
            local_tools = [t.tool_name for t in local_res.tool_calls]
            local_missing = [k for k in item["match_keys"] if k.lower() not in local_text.lower()]
            print(f"     [Local] Done in {local_dur}s | Tools: {local_tools} | Missing: {len(local_missing)}/{len(item['match_keys'])}", flush=True)
        except Exception as exc:
            local_dur = round(time.time() - t0, 2)
            local_text = f"ERROR: {exc}"
            local_tools = []
            local_missing = item["match_keys"]
            print(f"     [Local] FAILED ({exc})", flush=True)

        entry = {
            "id": item["id"],
            "prompt": item["prompt"],
            "gt_rows_count": len(gt_rows),
            "groq": {
                "duration_seconds": groq_dur,
                "tools": groq_tools,
                "missing_items": groq_missing,
                "answer_preview": groq_text[:300]
            },
            "local": {
                "duration_seconds": local_dur,
                "tools": local_tools,
                "missing_items": local_missing,
                "answer_preview": local_text[:300]
            }
        }
        results.append(entry)
        
        # Save intermediate results
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    db.close()
    print("\n" + "=" * 80, flush=True)
    print("VALIDATION SUITE COMPLETED SUCCESSFULLY", flush=True)
    print(f"Results saved to {output_file}", flush=True)
    print("=" * 80, flush=True)

if __name__ == "__main__":
    run_suite()
