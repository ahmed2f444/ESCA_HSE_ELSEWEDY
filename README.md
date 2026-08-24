# ESCA HSE Management System — Unified Platform

A full-stack, enterprise Health, Safety, and Environment (HSE) management platform for cable manufacturing operations (Elsewedy Cables — ESCA), featuring live IoT/AI telemetry monitoring, automated compliance checks, and a natural language AI agent.

---

## 🏗️ Architecture & Project Structure

```text
ESCA_HSE/
├── backend/          # Spring Boot 4 / Java 17 REST API & Core Business Logic
├── frontend/         # React 18 + Tailwind CSS Dashboard (RTL Arabic interface, Vite)
├── ai-agent/         # Python 3.12+ FastAPI AI Agent (Groq / Ollama Q&A + APScheduler Automation)
├── docs/             # Project Plan PDF, team handoff specs, contracts & architecture guides
└── docker-compose.yml
```

---

## 🌐 Live Cloud Database (Railway MySQL)

All services are connected directly to the central Railway MySQL cloud database:
- **Host**: `zephyr.proxy.rlwy.net`
- **Port**: `17885`
- **Database**: `railway`
- **Tables**: 135 structured domain tables (`incidents`, `permits`, `capa`, `chemicals`, `certificates`, `ppe_inventory`, `risk_register`, `sensor_readings`, `fire_equipment`, etc.)

### 🛡️ Architectural Guardrails
- **Read Operations**: The AI Agent performs direct, fast SQL read queries via SQLAlchemy connection pooling across all tables.
- **Write / Mutation Operations**: The AI Agent **NEVER writes directly to the database**. All automated state mutations (flagging overdue permits, creating training certificate reminders, CAPA escalations, risk review flags) are dispatched through Spring Boot's internal automation endpoint (`POST /api/v1/internal/automation/actions`) with service authentication and idempotency keys to enforce business validation and preserve the audit trail.
- **Environment Isolation**: Credentials and connection URLs are loaded from `.env` files in each service.

---

## 🚀 Quickstart Guide

### Option 1: Running with Docker Compose

Spin up all services (Backend on `8080`, AI Agent on `8000`, Frontend on `5180`):

```bash
docker compose up --build
```

Access the dashboard at: **http://localhost:5180**

---

### Option 2: Running Services Locally

#### 1. Backend (Spring Boot API)
```bash
cd backend
mvn spring-boot:run
```
*Health Check*: `http://localhost:8080/api/v1/health`

#### 2. AI Agent & Automation Service (FastAPI)
```bash
cd ai-agent
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Health Check*: `http://localhost:8000/health`
*API Docs*: `http://localhost:8000/docs`

#### 3. Frontend (React Dashboard)
```bash
cd frontend
npm install
npm run dev -- --port 5180
```
*Web Dashboard*: `http://localhost:5180`

---

## 🧪 Testing & Verification

- **AI Agent Live Integration Tests**:
  ```bash
  cd ai-agent
  .\venv\Scripts\python.exe -m pytest tests/test_live_integration.py -v
  ```
- **Backend Test Suite**:
  ```bash
  cd backend
  mvn test
  ```
- **Frontend Production Build**:
  ```bash
  cd frontend
  npm run build
  ```

---

## 📚 Documentation

Detailed documentation, architecture specs, and contracts can be found in the [`docs/`](./docs) directory:
- [`docs/ESCA_HSE_Project_Plan.pdf`](./docs/ESCA_HSE_Project_Plan.pdf)
- [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md)
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
- [`docs/SPRING_INTEGRATION_CONTRACT.md`](./docs/SPRING_INTEGRATION_CONTRACT.md)
- [`docs/FRONTEND_DOCS.md`](./docs/FRONTEND_DOCS.md)
- [`docs/AGENT_VERIFICATION_REPORT.md`](./docs/AGENT_VERIFICATION_REPORT.md)
