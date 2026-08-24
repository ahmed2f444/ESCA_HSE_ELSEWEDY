# Spring Integration Contract for HSE Automation

Status: **Proposed v1 for team agreement**

Event schema version: **1.0**

This document defines the boundary between the Python automation worker and
the Spring Boot backend. It is intentionally strict: Python detects candidates
from MySQL using a read-only account, while Spring remains the only component
allowed to apply business changes, create durable audit records, and request
notifications.

## 1. Safety model

The safe default is:

```dotenv
AUTOMATION_DELIVERY_MODE=dry_run
AUTOMATION_LIVE_ENABLED=false
```

In this mode the worker validates and counts planned events without acquiring
a token or making an HTTP request. `delivered_count` is always `0`.

Live delivery requires two independent gates:

```dotenv
AUTOMATION_DELIVERY_MODE=spring
AUTOMATION_LIVE_ENABLED=true
```

The worker must fail closed when only one gate is enabled, when credentials are
missing, or when the remote URL violates the client security rules. Non-local
Spring URLs require HTTPS.

Enabling both gates is an operational decision, not a developer convenience.
It is allowed only after the backend team has implemented this contract and the
integration acceptance tests in section 13 pass.

## 2. Ownership boundary

### Python owns

- read-only candidate detection;
- schedule evaluation;
- deterministic event IDs and idempotency keys;
- an allowlisted, minimal payload without names, emails, descriptions, or other
  unnecessary free text;
- local contract validation before any request;
- best-effort transient retries inside the current worker process;
- aggregate, non-sensitive logs.

### Spring owns

- service authentication and authorization;
- reloading the target entity from the authoritative database;
- revalidating current state, tenant/project scope, rule, action, and payload;
- enforcing idempotency with a unique persisted key;
- applying the business effect;
- persisting the audit record and notification intent;
- transaction boundaries and concurrency control;
- producing in-app/email notifications through the approved backend flow;
- durable recovery, replay, monitoring, and incident handling.

Python must never write directly to operational HSE tables and must never be
treated as the final authority for whether an action is still applicable.

## 3. Fixed endpoints

The client may call only these paths relative to `SPRING_API_BASE_URL`:

| Purpose | Method and path |
|---|---|
| Obtain a service token | `POST /api/v1/internal/auth/service-token` |
| Submit one automation action | `POST /api/v1/internal/automation/actions` |

All supported rules use the same unified action endpoint. The `rule_id`,
`entity_type`, and `action` fields select the server-side handler.

The database column `automation_rules.action_endpoint` is legacy/sample
metadata. It is not trusted and is never used for runtime routing. Spring and
Python must not construct a URL from that value, even if it is present or later
changed in the database.

Dynamic per-rule URLs, redirects, and action URLs supplied by data are outside
this contract.

## 4. Service authentication

### Token request

```http
POST /api/v1/internal/auth/service-token
Content-Type: application/json
Cache-Control: no-store
```

```json
{
  "client_id": "esca-hse-automation",
  "client_secret": "<secret supplied outside Git>"
}
```

### Successful token response

```json
{
  "access_token": "<opaque bearer token>",
  "token_type": "Bearer",
  "expires_in": 900,
  "scope": "automation:write"
}
```

Requirements:

- the token must contain the `automation:write` scope;
- the service secret must be stored in the deployment secret manager, never in
  Git, logs, sample data, or an event payload;
- Spring should issue a short-lived token;
- the client caches the token in memory and refreshes it before expiry;
- one `401` during action delivery triggers one forced token refresh; a second
  `401` fails the operation;
- token responses and bearer values must never be logged.

## 5. Unified action request

One event is submitted per request:

```http
POST /api/v1/internal/automation/actions
Authorization: Bearer <token>
Idempotency-Key: hse-automation:v1:<64 lowercase hex characters>
X-Correlation-ID: evt_<32 lowercase hex characters>
X-Event-Schema-Version: 1.0
Content-Type: application/json
```

Body:

```json
{
  "schema_version": "1.0",
  "event_id": "evt_0123456789abcdef0123456789abcdef",
  "idempotency_key": "hse-automation:v1:<64 lowercase hex characters>",
  "rule_id": "AUT-001",
  "entity_type": "PERMIT",
  "entity_id": "PTW-2026-0406",
  "alert_code": "PERMIT_OVERDUE",
  "action": "FLAG_OVERDUE_PERMIT",
  "evaluated_at_utc": "2026-08-13T06:00:00Z",
  "business_date": "2026-08-13",
  "payload": {
    "permit_id": "PTW-2026-0406",
    "expiry_at": "2026-08-12T09:00:00Z",
    "status": "ACTIVE",
    "minutes_overdue": 1260
  }
}
```

`delivery_mode` is local worker state and must not appear in the Spring body.
Spring must verify that the `Idempotency-Key` header equals the body value and
that `X-Correlation-ID` equals `event_id`.

## 6. Supported rule contracts

| Rule | Entity type | Action |
|---|---|---|
| `AUT-001` | `PERMIT` | `FLAG_OVERDUE_PERMIT` |
| `AUT-002` | `CERTIFICATE` | `CREATE_TRAINING_REMINDER` |
| `AUT-003` | `CAPA` | `CREATE_CAPA_ESCALATION` |
| `AUT-004` | `RISK` | `FLAG_RISK_FOR_REVIEW` |

Spring must reject an unknown rule or any mismatch between rule, entity type,
and action. It must also reject payload fields outside the allowlist below.

### `AUT-001` permit payload

Required:

- `permit_id`
- `expiry_at`
- `status`
- `minutes_overdue`

Optional allowlisted identifiers/values:

- `department_id`
- `zone_id`
- `requester_id`
- `issuer_id`
- `risk_level`

### `AUT-002` certificate payload

Required:

- `certificate_id`
- `expiry_date`
- `status`
- `days_to_expiry`

Optional allowlisted identifiers:

- `employee_id`
- `manager_id`
- `course_id`

### `AUT-003` CAPA payload

Required:

- `capa_id`
- `due_date`
- `status`
- `days_overdue`
- `escalation_day`

Optional allowlisted identifiers/values:

- `incident_id`
- `finding_id`
- `assigned_to`
- `priority`

### `AUT-004` risk payload

Required:

- `risk_id`
- `inherent_score`
- `status`

Optional allowlisted identifiers/values:

- `department_id`
- `zone_id`
- `owner_id`
- `risk_level`
- `residual_score`
- `last_reviewed_at`
- `next_review_date`
- `days_since_review`

Spring must derive names, email addresses, message text, recipients, and UI
links from authoritative backend data. Python does not send them.

## 7. Server-side validation

Before applying an action, Spring must:

1. authenticate the service account and verify `automation:write`;
2. validate schema version, headers, field types, sizes, and allowlists;
3. load the target entity by `entity_type` and `entity_id`;
4. verify that the entity belongs to the expected project/company scope;
5. recompute whether the rule is still applicable at the supplied business
   time;
6. verify that referenced employees, departments, zones, and courses exist;
7. reject forbidden transitions and unsupported actions;
8. check the idempotency key before creating any side effect.

The Python result is a candidate signal. It is not permission to bypass normal
Spring business rules.

## 8. Successful and terminal outcomes

### Applied

HTTP `201`:

```json
{
  "status": "APPLIED",
  "event_id": "evt_0123456789abcdef0123456789abcdef",
  "action_record_id": "ACT-12345",
  "audit_id": "AUD-12345",
  "processed_at_utc": "2026-08-13T06:00:01Z"
}
```

### Duplicate

HTTP `200` when the same idempotency key was already completed:

```json
{
  "status": "DUPLICATE",
  "event_id": "evt_0123456789abcdef0123456789abcdef",
  "action_record_id": "ACT-12345",
  "audit_id": "AUD-12345",
  "processed_at_utc": "2026-08-13T06:00:01Z"
}
```

### No longer applicable

HTTP `409`:

```json
{
  "status": "NOT_APPLICABLE",
  "event_id": "evt_0123456789abcdef0123456789abcdef",
  "error_code": "ENTITY_STATE_CHANGED"
}
```

`NOT_APPLICABLE` is a handled terminal outcome, not a transport failure. Error
codes must be stable uppercase machine codes and must not include sensitive
details.

## 9. Permanent errors

Spring should use standard status codes:

| Status | Meaning |
|---|---|
| `400` or `422` | Invalid schema, header, field, or payload |
| `401` | Missing, expired, or invalid service token |
| `403` | Token lacks `automation:write` or violates scope |
| `404` | Target entity does not exist in the allowed scope |
| `409` | Valid `NOT_APPLICABLE` outcome or a documented conflict |

The Python client does not retry permanent validation or authorization errors.
Response bodies are never copied into logs or raised exception messages.

## 10. Retry and delivery semantics

The client may retry:

- transport/connect/read failures;
- HTTP `429`, honoring a bounded `Retry-After` when valid;
- HTTP `500`, `502`, `503`, and `504`.

The maximum number of attempts is configured by `SPRING_MAX_ATTEMPTS` and is
restricted by the client. Every retry preserves the same `event_id` and
idempotency key.

These retries are **best-effort and in-process only**:

- there is no durable Python outbox;
- there is no message broker or dead-letter queue in this service;
- pending events do not survive a worker crash or machine restart;
- a later failure can leave an earlier part of a batch applied;
- the next scheduled detection may rebuild the same stable event, but this is
  not a guaranteed replay mechanism.

Spring's unique idempotency constraint prevents duplicate business effects for
requests that are repeated. It does not make Python delivery durable.

Before production, the team must choose one of these or an equivalent design:

- a Spring-owned transactional outbox plus a notification worker; or
- a durable broker/queue with acknowledgement, retry, replay, and DLQ support.

The chosen design must include monitoring, alerting, retention, and a documented
operator replay procedure.

## 11. Idempotency, transaction, and audit requirements

For each first-time accepted event, Spring must atomically:

1. reserve the unique idempotency key;
2. revalidate the target state;
3. apply the business effect or create the approved action record;
4. persist an audit record containing the event ID, rule, target, outcome,
   service principal, and timestamps;
5. persist the notification intent/outbox record if a notification is required.

A retry with the same key must return the original successful identifiers and
must not create another effect or notification. Concurrent requests with the
same key must have the same behavior.

## 12. Configuration and logging

Supported worker settings:

```dotenv
AUTOMATION_DELIVERY_MODE=dry_run
AUTOMATION_LIVE_ENABLED=false
SPRING_API_BASE_URL=http://127.0.0.1:8080
SPRING_AUTOMATION_CLIENT_ID=esca-hse-automation
SPRING_AUTOMATION_CLIENT_SECRET=
SPRING_CONNECT_TIMEOUT_SECONDS=3
SPRING_READ_TIMEOUT_SECONDS=10
SPRING_MAX_ATTEMPTS=3
SPRING_TOKEN_REFRESH_LEEWAY_SECONDS=30
```

Deployment secrets must be injected by the environment or secret manager.
Neither side may log:

- passwords, client secrets, or bearer tokens;
- full request or response bodies;
- names, emails, descriptions, corrective-action text, or other unnecessary
  personal/free-text data;
- database connection strings or DSNs.

Allowed operational logs are aggregate counts, rule IDs, outcome classes,
status-code classes, durations, and sanitized error categories.

## 13. Integration acceptance criteria

Live mode remains disabled until the team demonstrates all of the following in
an integration environment:

1. the token endpoint issues a short-lived token with `automation:write`;
2. invalid credentials and missing scope are rejected;
3. all four rules are accepted only through the fixed unified action endpoint;
4. changing `automation_rules.action_endpoint` cannot alter the outbound URL;
5. malformed and over-permissive payloads are rejected before side effects;
6. Spring revalidation returns `NOT_APPLICABLE` for changed entity state;
7. concurrent duplicate requests create one business effect, audit record, and
   notification intent;
8. `429` and transient `5xx` retries preserve the idempotency key;
9. permanent `4xx` errors are not retried;
10. logs and errors expose no secrets, payload bodies, or PII;
11. database read-only checks still pass for the Python service;
12. the chosen durable outbox/broker design and operational recovery procedure
    are approved, or the team explicitly accepts best-effort delivery for the
    training demo.

## 14. Team decisions still required

- final shared table and identifier mappings;
- Spring service-account provisioning and secret rotation;
- the authoritative recipient/notification rules;
- audit retention and access permissions;
- durable outbox or broker ownership;
- monitoring, alert thresholds, and replay ownership;
- deployment URL, TLS certificate, firewall, and rate limits;
- whether the raw development detection endpoint is removed or protected by
  authenticated role checks before deployment.

Until those decisions are complete, `dry_run` is the supported project-ready
mode and both live gates must remain off.
