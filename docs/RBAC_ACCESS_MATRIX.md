# ESCA HSE RBAC Access Matrix

Status: implemented in Spring Boot and consumed by the React application.

The authoritative runtime policy is
`backend/src/main/java/com/esca/hse/security/RbacPolicy.java`. The web
application uses the permission list returned by the login and `/auth/me`
responses, but Spring remains the security boundary.

## Access grades

- `C`: create
- `R`: read
- `U`: update
- `D`: delete
- `NONE`: no access
- `SELF`: create/read the signed-in employee's records only
- `AGGREGATE`: non-identifying medical summaries only
- `FITNESS`: the signed-in employee's fitness result only

## Canonical role matrix

| Role | Data scope | Incidents | Permits | Inspections / PPE / Fire | Risks / JSA / HazMat | Training | Occupational health | Administration | High-risk approval | Export |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| System Administrator | Site | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | RW | Yes | Yes |
| HSE Manager | Site | CRUD | CRUD | CRUD | CRUD | CRUD | Aggregate | RW | Yes | Yes |
| HSE Officer | Assigned zones | CRU | CRU | CRUD | CRU | CRUD | Fitness | NONE | No | Yes |
| Occupational Doctor | Clinic | C | NONE | CR | NONE | SELF | CRUD | NONE | No | No |
| Department Manager | Department | CR | R | R | R | R | Fitness | NONE | No | Yes |
| Shift Supervisor | Shift | CR | CR | CR | NONE | SELF | Fitness | NONE | No | No |
| Maintenance Technician | Assigned work | C | CR | CR | NONE | SELF | Fitness | NONE | No | No |
| Worker | Self | C | CR | CR | NONE | SELF | Fitness | NONE | No | No |
| Contractor | Active permit | C | CR | CR | NONE | SELF | Fitness | NONE | No | No |
| Auditor | Site read-only | R | R | R | R | R | NONE | R | No | Yes |
| Automation Service | Service API | R | R | R | R | R | NONE | Service API only | No | No |

`SYSTEM_ADMINISTRATOR` is an operational compatibility role. The ten roles
from the project RBAC sheet remain unchanged.

## Special enforcement rules

1. Unauthenticated API calls return `401`; authenticated calls without the
   required permission return `403`.
2. Unknown roles and newly added, unclassified API routes are denied by
   default.
3. Auditor access is read-only, including administration and audit views.
4. Identifiable occupational-health records are limited to the Occupational
   Doctor and System Administrator. HSE Manager receives aggregate results;
   other eligible employees receive only self-fitness access.
5. Approve/verify endpoints require the high-risk approval flag. Export and
   management-report delivery require the export flag.
6. Normal human roles can read suggestions and submit questions to the AI
   assistant. This grants no direct database authority to the agent.
7. `AUTOMATION_SERVICE` is not a human login. It uses a short-lived service JWT
   and is restricted to `/api/v1/internal/automation/**` with the
   `automation:write` scope.
8. Notification acknowledgement is allowed for signed-in human users. Other
   dashboard operations remain read-only.

## Route families

| Route family | RBAC module |
|---|---|
| `/dashboard`, `/field`, `/notifications` | Dashboard |
| `/incidents`, `/capa` | Incidents |
| `/permits` | Permits |
| `/inspections`, `/findings`, `/ppe`, `/fire`, `/fixed-safety`, `/iot` | Inspections |
| `/risks`, `/risk`, `/jsa`, `/hazmat` | Risks |
| `/training` | Training |
| `/occupational-health` | Health, Health Aggregate, or Health Self |
| `/master-data`, `/organization`, `/security`, `/integrations`, `/automation-rules` | Administration |
| `/audit` | Audit |
| `/reports` | Reports |
| `/agent`, `/ai/ask`, `/ai/suggestions` | AI Agent |

HTTP methods map to actions: `GET/HEAD/OPTIONS` to read, `POST` to create,
`PUT/PATCH` to update, and `DELETE` to delete. Paths containing `approve` or
`verify` map to approval. The management report send route maps to export.

## Authentication response contract

After login, Spring returns the canonical role, data scope, optional scope and
employee identifiers, and an effective permission list such as
`INCIDENTS:CREATE`. The JWT carries the same scope metadata. The frontend uses
this server response to hide inaccessible pages and actions; frontend hiding
alone is never treated as authorization.

## Adding or changing access

1. Add the route family to `RbacAuthorizationFilter` (unclassified routes are
   intentionally blocked).
2. Update `RbacPolicy` rather than adding role checks to individual pages.
3. Add policy unit tests and authenticated integration tests for both an
   allowed role and a denied role.
4. Update this matrix and run the complete backend and frontend verification.
