# 🛡️ ESCA HSE Management System — Unified Enterprise Platform

[![Spring Boot](https://img.shields.io/badge/Backend-Spring%20Boot%204%20%2F%20Java%2017-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/AI%20Agent-FastAPI%20%2F%20Python%203.12-blue.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2F%20Vite%20%2F%20TailwindCSS-61DAFB.svg)](https://react.dev/)
[![Security](https://img.shields.io/badge/Security-Hardened%20RBAC%20%26%20Parameterized%20SQL-success.svg)](#-security--rbac-architecture)
[![Database](https://img.shields.io/badge/Database-Railway%20MySQL%208-orange.svg)](#-live-cloud-database-railway-mysql)

A full-stack, enterprise-grade Health, Safety, and Environment (HSE) management platform designed for industrial cable manufacturing facilities (Elsewedy Cables — ESCA). The platform combines real-time IoT telemetry, computerized permit-to-work workflows, incident tracking, automated compliance engines, and a natural language AI conversational assistant.

---

## 🏗️ Architecture & Project Structure

```text
ESCA_HSE/
├── backend/          # Spring Boot 4 / Java 17 REST API & Enterprise Business Logic
├── frontend/         # React 18 + Tailwind CSS Dashboard (Modern RTL Arabic Interface, Vite)
├── ai-agent/         # Python 3.12+ FastAPI AI Agent (LLM Q&A + APScheduler Compliance Engine)
├── docs/             # Technical specifications, API contracts, and architecture guides
└── docker-compose.yml
```

---

## 🔒 Security & RBAC Architecture

The system enforces strict multi-tiered security protocols:
- **SQL Injection Prevention:** 100% parameterized queries with compile-time table whitelisting and dynamic query sanitization.
- **IDOR Mitigation:** Server-side ownership and role verification on all critical entity mutations (Permits approval/suspension, CAPA verification, Incident closing, equipment servicing).
- **Backend-Enforced RBAC:** Role-Based Access Control mapped across all route patterns (`/api/**` and `/api/v1/**`) with standardized JSON responses for `401 Unauthorized` and `403 Forbidden`.
- **Sensitive Data Safeguards:** AI tools filter and redact sensitive columns (`password_hash`, tokens, secrets) preventing unauthorized data inspection.

---

## 🌐 Live Cloud Database (Railway MySQL)

All services connect directly to the central Railway MySQL cloud instance:
- **Host**: `zephyr.proxy.rlwy.net`
- **Port**: `17885`
- **Database**: `railway`
- **Tables**: 135 structured domain tables (`incidents`, `permits`, `capa`, `chemicals`, `certificates`, `ppe_inventory`, `risk_register`, `sensor_readings`, `fire_equipment`, etc.)

### 🛡️ Architectural Guardrails
- **Read Operations**: The AI Agent performs fast, direct SQL read queries via SQLAlchemy connection pooling across all domain tables.
- **Write / Mutation Operations**: The AI Agent **never writes directly to the database**. All automated state mutations (overdue permit flagging, training certificate reminders, CAPA escalations, risk reviews) are dispatched through Spring Boot's internal automation endpoint (`POST /api/v1/internal/automation/actions`) using `SCOPE_automation:write` service JWTs and idempotency keys to enforce business validation and preserve complete audit trails.

---

## 🚀 Quickstart Guide

### Option 1: Running with Docker Compose

Spin up all services simultaneously (Backend on `8080`, AI Agent on `8000`, Frontend on `5180`):

```bash
docker compose up --build
```

Access the dashboard at: **http://localhost:5180**

---

### Option 2: Running Services Locally

#### 1. Backend (Spring Boot API)
```bash
cd backend
./mvnw spring-boot:run
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
*API Documentation (Swagger)*: `http://localhost:8000/docs`

#### 3. Frontend (React Dashboard)
```bash
cd frontend
npm install
npm run dev -- --port 5180
```
*Web Dashboard*: `http://localhost:5180`

---

## 🧪 Testing & Verification

- **Backend Test Suite (38/38 Tests Passing)**:
  ```bash
  cd backend
  ./mvnw test
  ```
- **AI Agent Live & Automation Tests (18/18 Tests Passing)**:
  ```bash
  cd ai-agent
  .\venv\Scripts\python.exe -m pytest tests/ -v
  ```
- **Frontend Production Build**:
  ```bash
  cd frontend
  npm run build
  ```

---

## 📚 Documentation & Specifications

Detailed documentation, architecture specs, and contracts are located in the [`docs/`](./docs) directory:
- [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md) — Public and internal API endpoints specification
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — System components & data flow architecture
- [`docs/SPRING_INTEGRATION_CONTRACT.md`](./docs/SPRING_INTEGRATION_CONTRACT.md) — Automation service integration contract
- [`docs/FRONTEND_DOCS.md`](./docs/FRONTEND_DOCS.md) — UI design tokens and component hierarchy
- [`docs/AGENT_VERIFICATION_REPORT.md`](./docs/AGENT_VERIFICATION_REPORT.md) — AI Agent testing and verification report

