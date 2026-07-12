# Session Log — 07-12-2026 (Session 2)

## TL;DR

* **Goal:** Implement authentication, authorization, and production operations hardening before public exposure.
* **Accomplished:** Shipped JWT-backed auth, role-based access control, page-level protection, structured production logging, and a production Docker Compose stack.
* **Branch:** `feat/phase-7-auth`

## Work Completed

* Added the `auth_users` table (Alembic revision `337ec2aab671_add_auth_users_table`) with role-based `AppUser` records (`USER`, `OPERATOR`, `ADMIN`), each linked one-to-one to a ledger account via a non-null foreign key so user creation stays atomic with ledger initialisation.
* Implemented JWT auth services and FastAPI dependencies: `get_current_user`, `get_optional_current_user`, `RoleChecker`, and `require_role`. Tokens are read from the `session_token` cookie first, then the `Authorization: Bearer` header.
* Added `/login` and `/register` page routes with `login.html` and `register.html` templates, plus a global 401 handler that redirects HTML page requests to `/login` while preserving JSON error responses for API clients.
* Applied operator/admin gating to correction and review workflows through `require_role` dependencies on the affected endpoints.
* Added the `edgebook.auth.cli` management CLI for seeding operator/admin accounts without manual SQL.
* Refactored `utils/logging.py` to emit single-line JSON records when `ENV=production` and added a production Compose stack (`docker-compose.prod.yml`) with migrate, app, ingestion-worker, and Postgres services plus healthchecks and restart policies.
* Extended test coverage with `tests/auth/test_endpoints.py` and `tests/auth/test_services.py`, and broadened `tests/api/test_pages.py` for authenticated page flows.

## Verification

* Auth and logging unit/integration tests added across `tests/auth/`, `tests/api/test_pages.py`, and `tests/utils/test_logging.py`.
* OpenAPI contract regenerated for the new auth and user endpoints.

## Decisions Made

* Bind `auth_users.account_id` with a non-null foreign key to guarantee ledger integration; simulate "no account" states by toggling `account.is_active`, never by clearing the foreign key.
* Read the session token from cookies first to support browser sessions, then fall back to the `Authorization` header for API clients.
* Keep JSON log formatting gated on `ENV=production` so local development retains human-readable output.
