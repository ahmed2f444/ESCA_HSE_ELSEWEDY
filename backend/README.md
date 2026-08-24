# ESCA HSE Spring API

Canonical Spring Boot 4 REST backend for the unified ESCA HSE platform.

It provides the complete MySQL domain schema, HSE CRUD and workflow APIs,
dashboard and reporting queries, field-task aggregation, JWT/RBAC security,
audit trails, notifications, PPE/fire/fixed-asset modules, and the secured
idempotent boundary used by the Python automation service.

Configuration is environment based. Use a local MySQL database for development
and keep all credentials in untracked environment files.

Stable routes are documented in `../docs/API_CONTRACT.md`.
