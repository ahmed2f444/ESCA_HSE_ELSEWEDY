# Run locally

## 1. Prerequisites

- MySQL 8.4 running on port `3306`
- Java 17 and Maven 3.9+
- Node.js 22.13+ and pnpm
- Python 3.14 for the automation service

Real credentials must only exist in untracked `.env` files. The Railway
database is not needed for local development and should not be used while
testing schema or workflow changes.

## 2. Prepare local MySQL

From the project root, run the guided setup:

```powershell
.\scripts\Setup-LocalDatabase.ps1
```

It prompts for the MySQL root password, a new Spring application password and
a separate read-only automation password. None is committed. To perform the
same operation manually, replace both password tokens in a local copy and run:

```sql
SOURCE C:/path/to/ESCA_HSE_Unified/database/000_local_bootstrap.sql;
```

The bootstrap creates `esca_hse`, `hse_app`, and `esca_automation_ro`.

## 3. Start the Spring API

Open a PowerShell terminal:

```powershell
cd backend
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "esca_hse"
$env:DB_USERNAME = "hse_app"
$env:DB_PASSWORD = "your-local-password"
$env:APP_SECURITY_ENABLED = "false"
mvn test
mvn spring-boot:run
```

Spring creates missing tables, loads synthetic demo records and listens on
`http://localhost:8080`. Check
`http://localhost:8080/api/v1/health` before starting the web applications.

For the complete JWT/RBAC demo set `APP_SECURITY_ENABLED=true` and use one of
the seeded local users below. They all use the local-only password
`HseDemo@2026`:

| User | Role |
|---|---|
| `hse.manager` | HSE manager |
| `hse.officer` | HSE officer |
| `department.manager` | Department manager |
| `worker` | Field worker |
| `auditor` | Auditor |

These accounts are development fixtures. Disable demo seeding and replace all
credentials before any hosted deployment.

## 4. Start the admin web application

Create `apps/admin-web/.env.local` from `.env.example`. Set
`NEXT_PUBLIC_REQUIRE_AUTH=true` only when Spring security is enabled.

```powershell
cd apps/admin-web
pnpm install
pnpm dev -- --port 3100
```

Open `http://localhost:3100`.

## 5. Start the field PWA

Create `apps/field-web/.env.local` from `.env.example` and use the same auth
setting as the admin app.

```powershell
cd apps/field-web
pnpm install
pnpm dev -- --port 3200
```

Open `http://localhost:3200`. The field app queues submissions locally while
offline and retries them after the browser reconnects.

## 6. Start safe AI automation

Create `services/automation/.env` from `.env.example`. Give its MySQL account
read-only access and keep both delivery safety settings unchanged.

```powershell
cd services/automation
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --reload --port 8000
```

In a separate terminal, start the scheduled worker:

```powershell
cd services/automation
.venv\Scripts\Activate.ps1
python -m app.worker
```

The safe defaults are:

```dotenv
AUTOMATION_DELIVERY_MODE=dry_run
AUTOMATION_LIVE_ENABLED=false
```

With these values the worker detects and plans events but does not call Spring
and does not mutate HSE business data. Live delivery requires an explicit
security review, matching service credentials at both services and changing
both switches deliberately.

## 7. Production-build checks

```powershell
cd backend
mvn test

cd ..\apps\admin-web
pnpm lint
pnpm build

cd ..\field-web
pnpm lint
pnpm build
```
