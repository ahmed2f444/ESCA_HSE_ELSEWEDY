# Recovered Session: `3b41c4d1-84df-451a-9fa3-74db9415075c`

**Date recovered:** 2026-08-21
**Original Session ID:** `3b41c4d1-84df-451a-9fa3-74db9415075c`

---

## Turn 1: User Prompt

help me run the project

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess -Unique)`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Get-CimInstance Win32_Process -Filter "ProcessId = 19044" | Select-Object CommandLine | Format-List`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Invoke-RestMethod -Uri http://127.0.0.1:8000/health`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Invoke-WebRequest -Uri http://127.0.0.1:8000/ -MaximumRedirection 0 | Select-Object StatusCode, StatusDescription`

---

### Turn 1: Assistant Response

I've detected that a Python process running the ESCA HSE AI Agent FastAPI application is **already running on port 8000** under a background runner (likely started in a previous workspace session or as an active runtime). 

When you tried to run:
```powershell
.\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
It failed with **`[WinError 10013]`** because port `8000` is already bound to that existing process.

### Verification of the Running Instance
I performed a health check on the currently running service:
* **Endpoint**: `http://127.0.0.1:8000/health`
* **Status**: `ok` (Connected to MySQL database `"railway"`, LLM: `Groq + local Ollama`).

---

### What would you like to do?

We have three options to proceed:

1. **Option 1: Use the already running service**
   The application is already running and accessible! You can open your web browser and navigate directly to:
   👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

2. **Option 2: Run the project on a different port**
   If you want to run a separate reloadable instance side-by-side using your virtual environment, you can run:
   ```powershell
   .\venv\Scripts\uvicorn.exe app.main:app --reload --port 8001
   ```
   Then access it at **[http://127.0.0.1:8001/](http://127.0.0.1:8001/)**.

3. **Option 3: Stop the existing process and restart on Port 8000**
   If you want to stop the existing process so you can free up port 8000 for your manual uvicorn reload command:
   * **PID of active process**: `19044`
   * You can stop it by running this in PowerShell:
     ```powershell
     Stop-Process -Id 19044 -Force
     ```
   * And then rerun your command:
     ```powershell
     .\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
     ```

Please let me know how you'd like to proceed!

---

## Turn 2: User Prompt

yea pls give me the employees list with their departments
⚠️ Error communicating with the agent:

Failed to fetch

If using Local Ollama, ensure ollama serve is running.

when i sent that can you fix this ?

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Stop-Process -Id 19044 -Force`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe test_agent.py`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe -X utf8 test_agent.py`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe -u -X utf8 test_agent.py`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Invoke-WebRequest -Uri https://api.groq.com/openai/v1/models -Headers @{ Authorization="Bearer gsk_REDACTED_FOR_SECURITY" }`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Resolve-DnsName api.groq.com`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Test-NetConnection -ComputerName api.groq.com -Port 443`

---

#### Tool Call: Created File

**Target File:** `C:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent\scratch\test_groq.py`

```python
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
base_url = os.getenv("GROQ_BASE_URL")
model = os.getenv("GROQ_MODEL")

print(f"API KEY: {api_key[:10]}...{api_key[-10:] if api_key else ''}")
print(f"BASE URL: {base_url}")
print(f"MODEL: {model}")

client = OpenAI(api_key=api_key, base_url=base_url)

print("\nListing models...")
try:
    models = client.models.list()
    print("Available models:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTrying simple completion...")
try:
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hello"}],
        timeout=10
    )
    print(f"Success! Response: {res.choices[0].message.content}")
except Exception as e:
    print(f"Error creating completion: {e}")

```

---

#### Tool Call: Created File

**Target File:** `C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\test_groq.py`

```python
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load from the workspace root .env
workspace_env = r"c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent\.env"
load_dotenv(workspace_env)

api_key = os.getenv("GROQ_API_KEY")
base_url = os.getenv("GROQ_BASE_URL")
model = os.getenv("GROQ_MODEL")

print(f"API KEY: {api_key[:10]}...{api_key[-10:] if api_key else ''}")
print(f"BASE URL: {base_url}")
print(f"MODEL: {model}")

client = OpenAI(api_key=api_key, base_url=base_url)

print("\nListing models...")
try:
    models = client.models.list()
    print("Available models:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTrying simple completion...")
try:
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hello"}],
        timeout=10
    )
    print(f"Success! Response: {res.choices[0].message.content}")
except Exception as e:
    print(f"Error creating completion: {e}")

```

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe "C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\test_groq.py"`

---

#### Tool Call: Created File

**Target File:** `C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\check_db.py`

```python
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

workspace_env = r"c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent\.env"
load_dotenv(workspace_env)

db_url = os.getenv("DATABASE_URL")
print(f"Connecting to database: {db_url}")

engine = create_engine(db_url)
with engine.connect() as conn:
    # Check tables
    res = conn.execute(text("SHOW TABLES"))
    tables = [r[0] for r in res.fetchall()]
    print(f"Tables in DB: {tables}")
    
    # Check count in employees
    if "employees" in tables:
        count = conn.execute(text("SELECT COUNT(*) FROM employees")).scalar()
        print(f"Employees count: {count}")
        if count > 0:
            sample = conn.execute(text("SELECT * FROM employees LIMIT 5")).fetchall()
            print("Sample employees:")
            for s in sample:
                print(s)
                
    # Check count in departments
    if "departments" in tables:
        count = conn.execute(text("SELECT COUNT(*) FROM departments")).scalar()
        print(f"Departments count: {count}")
        if count > 0:
            sample = conn.execute(text("SELECT * FROM departments LIMIT 5")).fetchall()
            print("Sample departments:")
            for s in sample:
                print(s)

```

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe "C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\check_db.py"`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe -X utf8 "C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\check_db.py"`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Invoke-WebRequest -Uri http://localhost:11434/ -MaximumRedirection 0`

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `Test-NetConnection -ComputerName localhost -Port 11434`

---

#### Tool Call: Created File

**Target File:** `C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\test_groq_agent.py`

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/ask"

payload = {
    "question": "yea pls give me the employees list with their departments",
    "model_mode": "groq"
}

print("Sending request with model_mode='groq'...")
try:
    res = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
    print(f"Status: {res.status_code}")
    data = res.json()
    print("Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Request failed: {e}")

```

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe -X utf8 "C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\test_groq_agent.py"`

---

#### Tool Call: Created File

**Target File:** `C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\test_auto_agent.py`

```python
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/ask"

payload = {
    "question": "yea pls give me the employees list with their departments",
    "model_mode": "auto"
}

print("Sending request with model_mode='auto'...")
start_time = time.time()
try:
    res = requests.post(CHAT_ENDPOINT, json=payload, timeout=60)
    elapsed = time.time() - start_time
    print(f"Status: {res.status_code} (took {elapsed:.2f}s)")
    data = res.json()
    print("Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Request failed after {elapsed:.2f}s: {e}")

```

---

#### Tool Call: Run Command

**Cwd:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent`

**Command:** `.\venv\Scripts\python.exe -X utf8 "C:\Users\ahmed\.gemini\antigravity-ide\brain\3b41c4d1-84df-451a-9fa3-74db9415075c\scratch\test_auto_agent.py"`

---

#### Tool Call: Modified File

**Target File:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent\app\agent.py`

**Target Content to Replace:**
```python
SYSTEM_PROMPT = """You are ESCA HSE Assistant — an expert Health, Safety & Environment AI with live read-only access to a MySQL database.

RULES:
1. Answer ONLY from the results of your MySQL tool calls — never invent names, IDs, dates, or statistics.
2. If a query returns no rows, say: "No matching records found in the database."
3. Always call a tool first before answering any factual question about current records.
4. Format answers with Markdown tables and bullet points. Include all returned rows — never omit records.
5. Reply in the user's language (English or Arabic)."""

SESSION_HISTORIES: dict[str, list[dict]] = {}

LOCAL_SYSTEM_PROMPT = """You are a concise HSE assistant with live read-only MySQL access.
For every factual question, use the relevant MySQL tool first — never answer from memory.
Use the purpose-built listing tools when one matches the request; use run_read_only_query for custom SQL.
Never invent values. Always answer from the tool result only."""

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
) -> AskResponse:
    # Both agents are MySQL-only; Excel KB is not used.
    if not session_id or session_id not in SESSION_HISTORIES:
        session_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        SESSION_HISTORIES[session_id] = [
            {
                "role": "system",
                "content": LOCAL_SYSTEM_PROMPT if model_mode == "local" else SYSTEM_PROMPT,
            }
        ]

    history = SESSION_HISTORIES[session_id]

    # Keep conversation history bounded to avoid exploding token sizes
    if len(history) > 9:
        history = [history[0]] + history[-8:]
        SESSION_HISTORIES[session_id] = history

    # An explicit database request must be answered from the live MySQL session.
    # Both agents are MySQL-only; no RAG context is injected.
    messages = list(history)
    messages.append({"role": "user", "content": question})

    traces: list[ToolCallTrace] = []
    max_loops = 4 if model_mode == "local" else 3
    seen_tool_calls: set[str] = set()
    last_model_used = None
    last_successful_result = None
    for i in range(max_loops):
        response, model_used = chat_completion(
            messages=messages,
            tools=TOOLS,
            local_tools=LOCAL_TOOLS,
            tool_choice="auto",
            model_mode=model_mode,
        )
        last_model_used = model_used
        message = response.choices[0].message

        # Check if model emitted tool calls
        if not message.tool_calls:
            content = (message.content or "").strip()

            # Self-healing: If model accidentally typed a SQL query in text instead of invoking a tool call
            embedded_sql = _extract_embedded_sql(content)
            if embedded_sql and i < max_loops - 1:
                handler = HANDLERS["run_read_only_query"]
                try:
                    result_data = handler(db=db, sql_query=embedded_sql)
                except Exception as exc:
                    result_data = {"error": str(exc)}

                traces.append(ToolCallTrace(
                    tool_name="run_read_only_query",
                    query_summary=f"Auto-executed embedded SQL: {embedded_sql[:60]}...",
                    rows_returned=int(result_data.get("returned_count", 0)) if isinstance(result_data, dict) else 0
                ))

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"Database query result for `{embedded_sql}`: {json.dumps(result_data, default=str)}\nNow present the final answer to the user clearly in Markdown without raw SQL."
                })
                continue

            # If conversational text without tool calls
            final_answer = content or (
                "No matching records were found in the Excel data for this request. "
                "Please provide an entity ID, sheet name, or more specific keyword."
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

                traces.append(ToolCallTrace(
                    tool_name=func_name,
                    query_summary=f"Executed {func_name} with args: {args}",
                    rows_returned=rows_count
                ))

                # Structure payload safely without breaking JSON string validity
                if isinstance(result_data, dict) and "rows" in result_data and isinstance(result_data["rows"], list):
                    trimmed = dict(result_data)
                    row_limit = 100 if func_name in {"search_excel_records", "query_excel_sheet", "list_chemicals"} else 5
                    trimmed["rows"] = result_data["rows"][:row_limit]
                    payload = json.dumps(trimmed, default=str)
                else:
                    payload = json.dumps(result_data, default=str)

                payload_limit = 16000 if func_name in {"search_excel_records", "query_excel_sheet", "list_chemicals"} else 6000
                if len(payload) > payload_limit:
                    payload = payload[:payload_limit] + "..."

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

    # Ollama can spend its final round repeating a tool call. Preserve the
    # successful database result instead of discarding it behind a loop error.
    if last_successful_result is not None:
        final_answer = (
            "The database query completed, but the local model did not format a "
            "final response. Retrieved result: "
            f"{json.dumps(last_successful_result, default=str)}"
        )
    else:
        final_answer = "The database query did not complete. Please ask a more specific question."
    SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
    SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})
    return AskResponse(
        session_id=session_id,
        answer=final_answer,
        tool_calls=traces,
        model_used=last_model_used,
    )
```

**Replacement Content:**
```python
SYSTEM_PROMPT = """You are ESCA HSE Assistant — an expert Health, Safety & Environment AI with live read-only access to a MySQL database.

KEY TABLES:
- departments: department_id (PK), name_ar, name_en, department_type, active_flag
- employees: employee_id (PK), display_name, department_id, zone_id, job_title, manager_id, employment_type, hire_date, email_alias, active_flag
- incidents: incident_id (PK), reported_at, department_id, zone_id, reported_by, incident_type, severity, title, description, injured_employee_id, lost_days, status, target_close_date, actual_close_date, source
- permits: permit_id (PK), permit_type, department_id, zone_id, work_description, requester_id, issuer_id, executor_type, executor_name, start_at, expiry_at, risk_level, status
- capa: capa_id (PK), incident_id, finding_id, title, action_type, priority, assigned_to, due_date, status, completion_date, days_overdue
- chemicals: chemical_id (PK), trade_name, chemical_name, cas_number, supplier, quantity, unit, ghs_classes, storage_class, zone_id
- ppe_inventory: ppe_item_id (PK), item_code, name_ar, category, unit, balance_qty, reorder_threshold, monthly_consumption, stock_status
- monthly_kpis: kpi_id (PK), month, hours_worked, recordable_incidents, lost_time_injuries, lost_days, near_misses, safety_observations, trir, ltifr
- ai_events: ai_event_id (PK), detected_at, event_type, camera_id, zone_id, employee_id, confidence_pct, severity, status, action_taken, linked_incident_id

RULES:
1. Answer ONLY from the results of your MySQL tool calls — never invent names, IDs, dates, or statistics.
2. If a query returns no rows, say: "No matching records found in the database."
3. Always call a tool first before answering any factual question about current records.
4. Format answers with Markdown tables and bullet points. Include all returned rows — never omit records.
5. Reply in the user's language (English or Arabic)."""

SESSION_HISTORIES: dict[str, list[dict]] = {}

LOCAL_SYSTEM_PROMPT = """You are a concise HSE assistant with live read-only MySQL access.

KEY TABLES:
- departments: department_id (PK), name_ar, name_en, department_type, active_flag
- employees: employee_id (PK), display_name, department_id, zone_id, job_title, manager_id, employment_type, hire_date, email_alias, active_flag
- incidents: incident_id (PK), reported_at, department_id, zone_id, reported_by, incident_type, severity, title, description, injured_employee_id, lost_days, status, target_close_date, actual_close_date, source
- permits: permit_id (PK), permit_type, department_id, zone_id, work_description, requester_id, issuer_id, executor_type, executor_name, start_at, expiry_at, risk_level, status
- capa: capa_id (PK), incident_id, finding_id, title, action_type, priority, assigned_to, due_date, status, completion_date, days_overdue
- chemicals: chemical_id (PK), trade_name, chemical_name, cas_number, supplier, quantity, unit, ghs_classes, storage_class, zone_id
- ppe_inventory: ppe_item_id (PK), item_code, name_ar, category, unit, balance_qty, reorder_threshold, monthly_consumption, stock_status
- monthly_kpis: kpi_id (PK), month, hours_worked, recordable_incidents, lost_time_injuries, lost_days, near_misses, safety_observations, trir, ltifr
- ai_events: ai_event_id (PK), detected_at, event_type, camera_id, zone_id, employee_id, confidence_pct, severity, status, action_taken, linked_incident_id

For every factual question, use the relevant MySQL tool first — never answer from memory.
Use the purpose-built listing tools when one matches the request; use run_read_only_query for custom SQL.
Never invent values. Always answer from the tool result only."""

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
) -> AskResponse:
    # Both agents are MySQL-only; Excel KB is not used.
    if not session_id or session_id not in SESSION_HISTORIES:
        session_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        SESSION_HISTORIES[session_id] = [
            {
                "role": "system",
                "content": LOCAL_SYSTEM_PROMPT if model_mode == "local" else SYSTEM_PROMPT,
            }
        ]

    history = SESSION_HISTORIES[session_id]

    # Keep conversation history bounded to avoid exploding token sizes
    if len(history) > 9:
        history = [history[0]] + history[-8:]
        SESSION_HISTORIES[session_id] = history

    # An explicit database request must be answered from the live MySQL session.
    # Both agents are MySQL-only; no RAG context is injected.
    messages = list(history)
    messages.append({"role": "user", "content": question})

    traces: list[ToolCallTrace] = []
    max_loops = 6 if model_mode == "local" else 5
    seen_tool_calls: set[str] = set()
    last_model_used = None
    last_successful_result = None
    for i in range(max_loops):
        response, model_used = chat_completion(
            messages=messages,
            tools=TOOLS,
            local_tools=LOCAL_TOOLS,
            tool_choice="auto",
            model_mode=model_mode,
        )
        last_model_used = model_used
        message = response.choices[0].message

        # Check if model emitted tool calls
        if not message.tool_calls:
            content = (message.content or "").strip()

            # Self-healing: If model accidentally typed a SQL query in text instead of invoking a tool call
            embedded_sql = _extract_embedded_sql(content)
            if embedded_sql and i < max_loops - 1:
                handler = HANDLERS["run_read_only_query"]
                try:
                     result_data = handler(db=db, sql_query=embedded_sql)
                except Exception as exc:
                     result_data = {"error": str(exc)}

                traces.append(ToolCallTrace(
                    tool_name="run_read_only_query",
                    query_summary=f"Auto-executed embedded SQL: {embedded_sql[:60]}...",
                    rows_returned=int(result_data.get("returned_count", 0)) if isinstance(result_data, dict) else 0
                ))

                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"Database query result for `{embedded_sql}`: {json.dumps(result_data, default=str)}\nNow present the final answer to the user clearly in Markdown without raw SQL."
                })
                continue

            # If conversational text without tool calls
            final_answer = content or (
                "No matching records were found in the Excel data for this request. "
                "Please provide an entity ID, sheet name, or more specific keyword."
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

                traces.append(ToolCallTrace(
                    tool_name=func_name,
                    query_summary=f"Executed {func_name} with args: {args}",
                    rows_returned=rows_count
                ))

                # Structure payload safely without breaking JSON string validity
                if isinstance(result_data, dict) and "rows" in result_data and isinstance(result_data["rows"], list):
                    trimmed = dict(result_data)
                    row_limit = 100 if func_name in {"search_excel_records", "query_excel_sheet", "list_chemicals"} else 5
                    trimmed["rows"] = result_data["rows"][:row_limit]
                    payload = json.dumps(trimmed, default=str)
                else:
                    payload = json.dumps(result_data, default=str)

                payload_limit = 16000 if func_name in {"search_excel_records", "query_excel_sheet", "list_chemicals"} else 6000
                if len(payload) > payload_limit:
                    payload = payload[:payload_limit] + "..."

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

    # Ollama can spend its final round repeating a tool call. Preserve the
    # successful database result instead of discarding it behind a loop error.
    if last_successful_result is not None:
        final_answer = (
            "The database query completed, but the model did not format a "
            "final response. Retrieved result: "
            f"{json.dumps(last_successful_result, default=str)}"
        )
    else:
        final_answer = "The database query did not complete. Please ask a more specific question."
    SESSION_HISTORIES[session_id].append({"role": "user", "content": question})
    SESSION_HISTORIES[session_id].append({"role": "assistant", "content": final_answer})
    return AskResponse(
        session_id=session_id,
        answer=final_answer,
        tool_calls=traces,
        model_used=last_model_used,
    )
```

---

#### Tool Call: Modified File

**Target File:** `c:\Users\ahmed\OneDrive\Documents\dev-projects vs code\agent\app\main.py`

**Target Content to Replace:**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException
from sqlalchemy import text
from app.routers import chat
from app.excel_rag import excel_kb
from app.database import engine

app = FastAPI(
    title="ESCA HSE AI Agent Service",
    description="MySQL-backed LLM Agent with Groq integration and function calling.",
    version="1.0.0"
)

# Include Chat & Agent Routes
app.include_router(chat.router)
```

**Replacement Content:**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.routers import chat
from app.excel_rag import excel_kb
from app.database import engine

app = FastAPI(
    title="ESCA HSE AI Agent Service",
    description="MySQL-backed LLM Agent with Groq integration and function calling.",
    version="1.0.0"
)

# Enable CORS for local file:/// requests and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Chat & Agent Routes
app.include_router(chat.router)
```

---
