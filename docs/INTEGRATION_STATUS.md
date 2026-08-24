# Integration status

## Final local assembly

The full non-conversational ESCA HSE training platform is now assembled in
this repository. No additional team submission is required to run the local
product.

| Component | State | Notes |
|---|---|---|
| Canonical MySQL schema | Complete | Versioned Spring schema covers organization, incidents, PTW, JSA, HIRA, inspections, CAPA, PPE, fire, training, HazMat, occupational health, notifications, audit and automation. |
| Spring Boot backend | Complete | CRUD, workflows, dashboard, reports, field tasks, JWT authentication, RBAC, audit and internal automation actions. |
| Admin web | Complete | Arabic RTL React interface connected to live APIs across all HSE modules. |
| Field web PWA | Complete | Responsive React replacement for Flutter with tasks, forms, notifications and an offline retry queue. |
| HSE automation | Complete in safe mode | Read-only detection, scheduling, deterministic events, preview, dry-run dispatch and an opt-in Spring client. |
| PPE and fire submission | Integrated | Reviewed MySQL Spring module included under the canonical v1 API. |
| Conversational AI | Excluded | No chatbot or conversational agent is part of this build. |

## Safety decisions

- MySQL is the single source of truth.
- Development and tests use local databases; no Railway write is required.
- Real credentials belong only in untracked `.env` files.
- Browser authentication can be enabled with `APP_SECURITY_ENABLED=true` and
  `NEXT_PUBLIC_REQUIRE_AUTH=true`.
- Automation stays `dry_run` unless both delivery safety switches and the
  Spring service credentials are deliberately configured.

## Verification gates

- Spring integration tests cover CRUD/workflows, reports, JWT/RBAC and the
  idempotent internal automation contract.
- Both React applications pass ESLint and production builds.
- The Python automation suite validates detection, events, scheduler,
  preview, dispatch, worker configuration and Spring client behavior.
- Git secret checks and whitespace checks are required before handoff.
