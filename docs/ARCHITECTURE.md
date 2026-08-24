# ESCA HSE architecture

## Runtime components

| Component | Port | Responsibility |
|---|---:|---|
| Admin Web | 3100 | Management, dashboards, reports and configuration |
| Field Web PWA | 3200 | Mobile-first reporting, permits, inspections and offline queue |
| Spring API | 8080 | Authentication, validation, business writes, audit and MySQL access |
| Automation API | 8000 | Read-only detection, preview and health endpoints |
| Automation Worker | n/a | Scheduled rule evaluation and safe action dispatch |
| MySQL | 3306/local | Single source of truth |

## Safety boundaries

1. Browser applications never connect to MySQL directly.
2. Spring owns all user-facing writes, validation and audit records.
3. Automation reads MySQL with a read-only account.
4. Automation actions are dry-run unless live delivery is explicitly enabled.
5. The conversational AI agent is not included in this build.

## Integration flow

```text
Admin Web ─┐
           ├──> Spring API ───> MySQL
Field PWA ─┘         ▲
                     │ verified internal action
Automation Worker ───┘
        │
        └── read-only queries ──> MySQL
```

Team submissions remain under `imports/`. Reviewed code is copied into the
canonical component that owns it.
