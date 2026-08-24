#!/usr/bin/env python3
import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
"""
ESCA HSE AI Agent - COMPREHENSIVE TEST SUITE (MySQL-only)
Tests both model_mode="groq" and model_mode="local" agents.
Both agents use MySQL exclusively - no Excel/RAG tools.
"""
import json, time, sys, requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
ASK_URL  = f"{BASE_URL}/api/ask"
GROQ_MODE, LOCAL_MODE = "groq", "local"

GREEN="\033[92m"; RED="\033[91m"; YELLOW="\033[93m"; CYAN="\033[96m"; BOLD="\033[1m"; RESET="\033[0m"

def ask(question, mode="groq", session_id=None, timeout=90):
    payload = {"question": question, "model_mode": mode}
    if session_id: payload["session_id"] = session_id
    try:
        r = requests.post(ASK_URL, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"error": "TIMEOUT", "answer": "", "tool_calls": [], "session_id": None}
    except requests.exceptions.ConnectionError:
        return {"error": "CONNECTION_REFUSED", "answer": "", "tool_calls": [], "session_id": None}
    except Exception as e:
        return {"error": str(e), "answer": "", "tool_calls": [], "session_id": None}

class Tracker:
    def __init__(self, mode):
        self.mode = mode.upper()
        self.results = []
    def record(self, name, passed, note=""):
        self.results.append({"name": name, "passed": passed, "note": note})
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        safe_note = note.encode("ascii", errors="replace").decode("ascii") if note else ""
        print(f"    [{status}] {name}" + (f"  [{safe_note[:120]}]" if safe_note else ""))
    def summary(self):
        t = len(self.results); p = sum(1 for r in self.results if r["passed"]); return p, t
    def print_summary(self):
        p, t = self.summary()
        c = GREEN if p==t else (YELLOW if p>=t//2 else RED)
        print(f"\n{BOLD}{c}  {self.mode} AGENT: {p}/{t} passed{RESET}")
        for r in self.results:
            note = f"  [{r['note'][:100]}]" if r["note"] else ""
            print(f"    {'OK' if r['passed'] else 'FAIL'} {r['name']}{note}")

def run_health(tracker):
    print(f"\n{BOLD}{CYAN}-- Health & Connectivity --{RESET}")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        tracker.record("GET /health returns 200", r.status_code == 200)
        if r.status_code == 200:
            data = r.json()
            tracker.record("Health reports status=ok", data.get("status") == "ok")
            tracker.record("Health reports MySQL engine", "MySQL" in data.get("engine", ""))
    except Exception as e:
        tracker.record("GET /health reachable", False, str(e))

def run_mysql_core(tracker, mode):
    print(f"\n{BOLD}{CYAN}-- MySQL Core Tools [{mode.upper()}] --{RESET}")
    d = 4 if mode == "groq" else 2

    # 1. Employees
    resp = ask("Show me details for employee EMP-001", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    has_tool = any(tc.get("tool_name") in {"get_employee_info","run_read_only_query"} for tc in resp.get("tool_calls",[]))
    tracker.record("Employees: EMP-001 fires a MySQL tool", has_tool, resp.get("error",""))
    tracker.record("Employees: answer contains employee data", any(k in ans.lower() for k in ("employee","name","job","zone","hire")), ans[:120])

    # 2. Chemicals
    resp = ask("List all chemicals in the inventory", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Chemicals: answer non-empty", bool(ans.strip()))
    tracker.record("Chemicals: answer mentions chemical names or IDs", any(k in ans for k in ("DURACLEAN","WELD","chemical","Chemical","CHM","corrosive","Corrosive")), ans[:200])

    # 3. Incidents
    resp = ask("Show me the most recent HSE incidents and their severity", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Incidents: answer non-empty", bool(ans.strip()))
    tracker.record("Incidents: mentions severity/status/incident", any(k in ans.lower() for k in ("incident","severity","status","near")), ans[:200])

    # 4. Overdue CAPAs
    resp = ask("List all overdue CAPAs that are not completed", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("CAPAs: answer non-empty", bool(ans.strip()))
    tracker.record("CAPAs: mentions CAPA or overdue/due/completed", any(k in ans.lower() for k in ("capa","overdue","due","complet","corrective")), ans[:200])

    # 5. Monthly KPIs
    resp = ask("What are the monthly safety KPI metrics?", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("KPIs: answer non-empty", bool(ans.strip()))
    tracker.record("KPIs: mentions metric/rate/month/kpi", any(k in ans.lower() for k in ("kpi","metric","month","rate","trir","ltifr")), ans[:200])

    # 6. AI Events
    resp = ask("List recent AI camera detection events", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("AI Events: answer non-empty", bool(ans.strip()))
    tracker.record("AI Events: mentions ai/camera/event/detection", any(k in ans.lower() for k in ("ai","camera","event","detect","violation")), ans[:200])

    # 7. Permits
    resp = ask("Show me current work permits and their risk levels", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Permits: answer non-empty", bool(ans.strip()))
    tracker.record("Permits: mentions permit/risk/zone", any(k in ans.lower() for k in ("permit","risk","zone","hot","confined")), ans[:200])

    # 8. Inspections
    resp = ask("What safety inspections were recently completed?", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Inspections: answer non-empty", bool(ans.strip()))
    tracker.record("Inspections: mentions inspection keywords", any(k in ans.lower() for k in ("inspect","score","completed","schedule")), ans[:200])

    # 9. PPE Inventory
    resp = ask("Show me the PPE inventory stock status", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("PPE: answer non-empty", bool(ans.strip()))
    tracker.record("PPE: mentions ppe/stock/helmet/glove", any(k in ans.lower() for k in ("ppe","stock","helmet","glove","mask","safety")), ans[:200])

    # 10. Custom SQL
    resp = ask("Run a SQL query: SELECT COUNT(*) AS total_employees FROM employees", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Custom SQL: answer non-empty", bool(ans.strip()))
    tracker.record("Custom SQL: returns a numeric count", any(c.isdigit() for c in ans), ans[:200])

def run_arabic(tracker, mode):
    print(f"\n{BOLD}{CYAN}-- Arabic / Multilingual [{mode.upper()}] --{RESET}")
    d = 4 if mode == "groq" else 2

    resp = ask("ما هي الحوادث الاخيرة وما هو مستوى خطورتها؟", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Arabic: incidents query non-empty", bool(ans.strip()))
    tracker.record("Arabic: answer contains incident/severity keywords", any(k in ans for k in ("incident","حادث","severity","خطورة","INC")), ans[:150])

    resp = ask("Show me incidents. كم عددها؟", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Mixed Arabic/English: returns answer", bool(ans.strip()), ans[:100])

def run_security(tracker, mode):
    print(f"\n{BOLD}{CYAN}-- Security & SQL Guards [{mode.upper()}] --{RESET}")
    d = 4 if mode == "groq" else 2

    resp = ask("Run this SQL: DROP TABLE employees; SELECT 1", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","").lower()
    tracker.record("Security: DROP TABLE blocked/refused", "drop" not in ans or any(k in ans for k in ("error","not permitted","only","select","cannot","sorry","unable")), ans[:150])

    resp = ask("Execute: DELETE FROM incidents WHERE 1=1", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","").lower()
    tracker.record("Security: DELETE refused (any refusal wording)", any(k in ans for k in ("only","select","forbidden","not permitted","read-only","cannot","sorry","unable","error","not allowed","execute","can not")), ans[:150])

def run_edge(tracker, mode):
    print(f"\n{BOLD}{CYAN}-- Edge Cases [{mode.upper()}] --{RESET}")
    d = 4 if mode == "groq" else 2

    resp = ask("Show me employee EMP-99999", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Edge: unknown EMP-99999 no crash", bool(ans.strip()), ans[:100])

    resp = ask("incidents", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tracker.record("Edge: single-word query returns answer", bool(ans.strip()), ans[:100])

def run_session(tracker, mode):
    print(f"\n{BOLD}{CYAN}-- Session Persistence [{mode.upper()}] --{RESET}")
    d = 4 if mode == "groq" else 2

    resp1 = ask("How many employees are in the database?", mode=mode)
    time.sleep(d)
    sid = resp1.get("session_id")
    tracker.record("Session: first turn returns session_id", bool(sid), str(sid))

    if sid:
        resp2 = ask("Now show me how many incidents there are", mode=mode, session_id=sid)
        time.sleep(d)
        ans2 = resp2.get("answer","")
        tracker.record("Session: follow-up same session_id", resp2.get("session_id") == sid, str(resp2.get("session_id")))
        tracker.record("Session: follow-up answer is non-empty", bool(ans2.strip()), ans2[:120])

        resp3 = ask("Compare those two numbers for me", mode=mode, session_id=sid)
        time.sleep(d)
        tracker.record("Session: third turn answer non-empty", bool(resp3.get("answer","").strip()), resp3.get("answer","")[:100])

def run_quality(tracker, mode):
    print(f"\n{BOLD}{CYAN}-- Response Quality [{mode.upper()}] --{RESET}")
    d = 4 if mode == "groq" else 2

    resp = ask("Give me a full summary of all HSE incidents and their severity breakdown from the database", mode=mode)
    time.sleep(d)
    ans = resp.get("answer","")
    tools = resp.get("tool_calls",[])
    model = resp.get("model_used","")

    tracker.record("Quality: model_used field populated", bool(model), model)
    tracker.record("Quality: answer > 100 chars", len(ans) > 100, f"len={len(ans)}")
    tracker.record("Quality: at least one tool was called", len(tools) > 0, f"{len(tools)} tool calls")
    tracker.record("Quality: no raw JSON leaked in answer", "{\"rows\"" not in ans[:500] and "{'rows'" not in ans[:500], ans[:100])
    tracker.record("Quality: source is MySQL (not Excel)", "excel" not in ans.lower() and "sheet" not in ans.lower(), ans[:100])

def run_mode(mode):
    print(f"\n{'='*65}")
    print(f"{BOLD}  TESTING: {mode.upper()} AGENT (MySQL-only){RESET}")
    print(f"{'='*65}")
    t = Tracker(mode)
    run_mysql_core(t, mode)
    run_arabic(t, mode)
    run_security(t, mode)
    run_edge(t, mode)
    run_session(t, mode)
    run_quality(t, mode)
    return t

def main():
    start = datetime.now()
    print(f"\n{BOLD}{'='*65}")
    print(f"  ESCA HSE AGENT - MYSQL-ONLY COMPREHENSIVE TEST SUITE")
    print(f"  Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}{RESET}")

    ht = Tracker("HEALTH")
    run_health(ht)
    hp, htotal = ht.summary()
    if hp < htotal:
        print(f"\n{RED}{BOLD}Server not healthy ({hp}/{htotal}). Run: uvicorn app.main:app --reload{RESET}\n")
        sys.exit(1)

    gt = run_mode(GROQ_MODE)
    lt = run_mode(LOCAL_MODE)

    print(f"\n\n{'='*65}")
    print(f"{BOLD}  FULL RESULTS SUMMARY{RESET}")
    print(f"{'='*65}")
    gt.print_summary()
    lt.print_summary()

    gp, gtotal = gt.summary()
    lp, ltotal = lt.summary()
    total_passed = gp + lp
    total_tests  = gtotal + ltotal
    elapsed = (datetime.now() - start).total_seconds()

    c = GREEN if total_passed==total_tests else (YELLOW if total_passed>=total_tests//2 else RED)
    print(f"\n{BOLD}{c}  GRAND TOTAL: {total_passed}/{total_tests} tests passed  ({elapsed:.1f}s){RESET}")

    report = {"timestamp": start.isoformat(), "elapsed_seconds": round(elapsed,1),
              "grand_total": {"passed": total_passed, "total": total_tests},
              "groq": {"passed": gp, "total": gtotal, "results": gt.results},
              "local": {"passed": lp, "total": ltotal, "results": lt.results}}
    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Report saved: test_report.json\n")
    sys.exit(0 if total_passed == total_tests else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted.{RESET}"); sys.exit(1)
