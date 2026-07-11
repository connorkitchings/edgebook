# Session Log — 2026-07-10 (Session 02)

## TL;DR

- **Goal**: Implement fictional accounts, an immutable double-entry ledger, and manual CFB intake.
- **Accomplished**: Added Alembic schema management, generic ledger and CFB modules, REST APIs, tests, and API/runbook documentation.
- **Blockers**: None.
- **Next**: Implement simulated bet placement against open CFB markets using `WAGER_STAKE` postings.
- **Branch**: `feat/project-initialization`

**Tags**: ["feature", "ledger", "cfb", "api", "database", "testing"]

---

## Context

- **Started**: 2026-07-10
- **Ended**: 20:25 EDT
- **User Request**: Implement Phase 1.1–1.2 generic ledger and manual CFB intake.

## Work Completed

### Implementation

- Added Alembic with a reversible initial migration for generic ledger accounts,
  journal entries, postings, teams, games, markets, and market quotes.
- Added SQLite and PostgreSQL migration triggers that reject updates or deletes
  of ledger journal entries and transaction postings.
- Added the isolated `edgebook.ledger` service boundary with atomic account
  inception, deposits, withdrawals, balance materialization, and statement reads.
- Added the separate `edgebook.cfb` boundary for manually entered team, game,
  market, and American-odds quote resources.
- Registered fictional-account and CFB routers in FastAPI; no endpoint performs
  real-money activity or external wagering.

### Tests and Verification

- Added migration-backed, temporary SQLite fixtures and API/service coverage for
  double-entry balancing, rollback safety, append-only records, CFB validation,
  market opening, and ledger isolation.
- `uv run ruff format . && uv run ruff check . && uv run pytest` — passed;
  64 tests passed with 86.35% coverage.
- `uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head` — passed.
- Local `GET /health` smoke test returned API and database status `ok`.

## Decisions Made

- Persist simulation-credit amounts as integer cents and return exact decimal
  strings at the API boundary.
- Group equal-and-opposite transaction postings under immutable journal entries;
  an internal equity account is the generic counterparty for inception and
  manual credit operations.
- Keep CFB models independent from ledger services. Markets move from `DRAFT`
  to `OPEN` only after their required valid quote pair is present.

## Next Steps

1. Add simulated bet placement that requires an open CFB market and posts a
   `WAGER_STAKE` journal entry.
2. Add final-score capture and settlement using `WAGER_PAYOUT` postings.
3. Introduce position references when wager lifecycle work requires them.

## Handoff Notes

- **Current state**: Phase 1.1 and 1.2 are complete, verified, and ready for a
  first Edgebook product commit.
- **Files to review first**: `src/edgebook/ledger/services.py`,
  `src/edgebook/cfb/services.py`, and the initial Alembic migration.
- **Blockers**: None.
- **Next priority**: Phase 1.3 simulated bet placement against `OPEN` markets.
- **Open questions**: Define wager/position identifiers and the bet request
  contract before implementing settlement.

---

**Session Owner**: Codex
