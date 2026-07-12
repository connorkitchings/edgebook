# Session Log — 07-11-2026 (8 - Phase 4 Delivery Hardening)

## TL;DR
- **Goal**: Verify recent Phase 4 work and harden deployment, API contracts, and quality gates.
- **Accomplished**: Added migration-gated Docker deployment, a generated OpenAPI contract, docs repairs, and automated regression coverage.
- **Blockers**: None; a static Alembic database URL defect was found during smoke testing and corrected.
- **Next**: Choose and implement the first production ingestion provider, then expand to the required independent sources.
- **Branch**: `feat/manual-betting-flow`

**Tags**: ["platform", "docker", "migrations", "api", "testing"]

---

## Work Completed

### Deployment and Database Safety
- Added a one-shot `migrate` Compose service. The app now waits for a successful `alembic upgrade head` before starting.
- Included Alembic configuration and revisions in the runtime image, with Alembic promoted to a runtime dependency.
- Updated `alembic/env.py` to use the application's `DATABASE_URL` when the default local URL is configured, while preserving explicit test overrides.
- Added `scripts/docker_smoke.sh` and `make docker-smoke`; the smoke test uses a fresh volume and ephemeral host port, verifies the head revision plus `/health`, and always cleans up.
- Added the smoke test to CI.

### API Contract and Documentation
- Replaced the hand-maintained `docs/api/openapi.yaml` with generated `docs/api/openapi.json` from FastAPI's runtime schema.
- Added `scripts/generate_openapi.py --check` and regression tests covering artifact parity and all ingestion routes.
- Documented the ingestion routes, repaired MkDocs navigation and stale home-page links, and fixed the analytics page's template context typing.

### Verification
- `uv run ruff format . --check` — passed.
- `uv run ruff check .` — passed.
- `uv run mypy src/` — passed.
- `uv run python scripts/generate_openapi.py --check` — passed.
- `uv run pytest` — 96 passed; 89.20% coverage.
- `uv run mkdocs build --strict` — passed.
- `bash scripts/docker_smoke.sh` — passed against a fresh Postgres volume.

## Decisions Made
- FastAPI's generated schema is the canonical checked-in API contract; drift fails tests.
- Docker migrations run as a dedicated one-shot service instead of in the web process.
- The smoke script always chooses an ephemeral host port to avoid interfering with an existing local server.

## Handoff Notes
- The feature work is complete but remains unstaged and uncommitted for review.
- Fixture-only ingestion remains intentional. The next data-platform phase needs provider selection, credentials, source terms, and at least three independent adapters.
- The migration smoke test exposed and resolved the previously hidden SQLite fallback in Alembic; retain the revision assertion in future deployment checks.

---

**Session Owner**: Codex
**Related**: Phase 4 delivery hardening
