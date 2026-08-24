# ESCA HSE API contract

All canonical browser endpoints use `/api/v1`. JSON is the exchange format and
JWT Bearer authentication is available for the browser clients.

## Platform routes

| Area | Routes |
|---|---|
| Health | `GET /api/v1/health` |
| Authentication | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Dashboard and field work | `GET /api/v1/dashboard`, `GET /api/v1/field/tasks` |
| Reports and audit | `GET /api/v1/reports/summary`, `GET /api/v1/audit` |
| Organization | `/api/v1/organization/{departments|zones|employees}` |
| Core HSE records | `/api/v1/{incidents|jsa|permits|risks|inspections|findings|capa}` |
| Supporting records | `/api/v1/{hazmat|occupational-health|notifications|sensor-events|automation-rules}` |
| Training | `/api/v1/training/{courses|certificates}` |
| PPE | `/api/v1/ppe/{items|matrix|transactions}` |
| Fire and fixed assets | `/api/v1/fire/{equipment|inspections}`, `/api/v1/safety/fixed-assets` |

Generic core, organization and training resources expose list, get, create,
update and delete operations. Business transitions use dedicated endpoints:

- `PATCH /api/v1/permits/{id}/activate|suspend|close`
- `PATCH /api/v1/incidents/{id}/close`
- `PATCH /api/v1/jsa/{id}/approve`
- `PATCH /api/v1/inspections/{id}/complete`
- `PATCH /api/v1/capa/{id}/complete|verify`
- `PATCH /api/v1/notifications/{id}/read`

## Automation integration

The Python service performs read-only detection. Optional approved business
actions cross the authenticated Spring boundary:

- `POST /api/v1/internal/auth/service-token`
- `POST /api/v1/internal/automation/actions`

The action endpoint validates the event schema and headers, re-checks current
business state, writes an audit record and notification, and enforces
idempotency. The full event contract is in
`services/automation/docs/SPRING_INTEGRATION_CONTRACT.md`.

## Security model

- Local presentation mode can leave `APP_SECURITY_ENABLED=false`.
- Integrated mode uses short-lived HS256 JWTs and role authorities.
- Delete operations are limited to HSE managers/officers.
- Audit access is limited to HSE managers/auditors.
- Internal automation actions require the `automation:write` service scope.

## Error envelope

Validation and server errors use a sanitized envelope such as:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "A safe user-facing message",
  "fieldErrors": {},
  "traceId": "generated-correlation-id"
}
```

Passwords, tokens, database URLs and exception internals are never returned.
