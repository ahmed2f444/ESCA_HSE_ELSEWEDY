# Live Automation Notifications

## Outcome

The automation scheduler no longer stops at event preview when live mode is
configured. It performs read-only detection in the AI service and sends each
candidate to Spring Boot, which creates an unread in-app notification.

## Data flow

1. APScheduler loads the active `AUT-001` to `AUT-004` rules from MySQL.
2. The AI service detects candidates using its read-only database session.
3. The session is rolled back and closed before any delivery begins.
4. Deterministic `spring` events are sent to the internal Spring endpoint.
5. Spring authenticates the service token, validates the entity's current
   state, rejects stale events, and applies idempotency.
6. Spring writes one `notifications` row, one `automation_actions` row, and
   one audit record in a single transaction.

The notification types cover overdue permits, certificate expiry, overdue
CAPA actions, and high-risk review reminders. They are available through the
existing dashboard and notifications APIs.

## Required configuration

The backend and AI service must use the same values:

```env
AUTOMATION_CLIENT_ID=esca-hse-automation
AUTOMATION_CLIENT_SECRET=replace-with-a-strong-shared-secret
```

The AI service also requires:

```env
SPRING_API_BASE_URL=http://localhost:8080
AUTOMATION_DELIVERY_MODE=spring
AUTOMATION_LIVE_ENABLED=true
ENABLE_SCHEDULER=true
```

Docker Compose supplies the internal URL `http://backend:8080` and enables
live delivery. In a non-local deployment, `SPRING_API_BASE_URL` must use
HTTPS.

## Safety guarantees

- Detection issues SELECT queries only, then rolls back and closes its
  database session before delivery starts.
- Contradictory live-mode settings fail closed during startup.
- Full event batches are validated before the first network request.
- Spring re-reads authoritative entity state before creating a notification.
- Retried jobs do not create duplicate notifications.
- Logs contain aggregate counts and error types, not credentials or event
  payloads.

To return temporarily to preview-only behavior, set both:

```env
AUTOMATION_DELIVERY_MODE=dry_run
AUTOMATION_LIVE_ENABLED=false
```
