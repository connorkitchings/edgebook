# Session Log — 2026-07-11 (Session 02)

## TL;DR (≤5 lines)
- **Goal**: Audit Phase 1, fix issues, then plan and implement Phase 2 (Product Hardening) and Phase 3 (Analytics).
- **Accomplished**: Fixed 5 Phase 1 issues; completed Phase 2A (ledger hardening + structured reasoning), 2B (alternative market lines), 2C (score correction workflow); completed Phase 3 (analytics with ROI, Sharpe ratio, drawdown, calibration, and chart-ready series).
- **Blockers**: None.
- **Next**: Commit work, then plan Phase 4 (External Ingestion).
- **Branch**: `feat/manual-betting-flow`

**Tags**: ["feature", "analytics", "ledger", "wagering", "cfb", "migration", "testing", "docs"]

---

## Context
- **Started**: ~11:00 EDT
- **Ended**: ~14:00 EDT
- **Duration**: ~3 hours
- **User Request**: Start session, ensure Phase 1 is complete, fix issues, then plan and implement Phase 2 and Phase 3.

## Work Completed

### Phase 1 Fixes (5 issues)

1. **`alembic/env.py`** — Added wagering model import so autogenerate detects wagering schema changes
2. **`src/edgebook/core/money.py`** — Extracted shared money utilities (`cents_to_string`, `decimal_to_cents`, `validate_credit_amount`) from `api/accounts.py` to eliminate cross-API-file imports
3. **ADR files** — Filled `adr-0001-initial-architecture.md` (modular monolith decision) and `data_modeling.md` (full data modeling guide)
4. **`docs/api/openapi.yaml`** — Fixed misplaced `GET /accounts/{id}/transactions` endpoint nested under `/bets/{bet_id}`
5. **`src/edgebook/cfb/services.py`** — Normalized enum assignment style (removed `.value` calls, using raw enum objects consistently)

### Phase 2A: Ledger Hardening & Structured Reasoning

- Added `reconcile_account_balance()` service + `POST /accounts/{id}/reconcile` endpoint
- Added `rationale_category` enum (7 categories) + `notes` field on Bet model
- Migration: `20260711_03_structured_reasoning_fields.py`

### Phase 2B: Alternative Market Lines

- Dropped `UNIQUE(game_id, market_type)` constraint
- Service layer enforces: one moneyline per game; spread/total unique per line
- Migration: `20260711_04_alternative_market_lines.py`

### Phase 2C: Score Correction Workflow

- Added `ScoreCorrection` audit model
- Implemented `correct_game_result()` with full audit trail (offsetting ADJUSTMENT entries)
- Added `post_adjustment()` to ledger services
- Added `PUT /cfb/games/{id}/correction` endpoint with admin-auth TODO placeholder
- Migration: `20260711_05_score_correction.py`

### Phase 3: Analytics

- Added `sport` column to `cfb_games` (default `"CFB"`) for multi-sport future-proofing
- Migration: `20260711_06_sport_column.py`
- Created `src/edgebook/analytics/` module with 7 service functions
- Created `GET /accounts/{id}/analytics` endpoint with date range and configurable bucket params
- Returns: summary (ROI, win rate, Sharpe ratio, max drawdown), by-sport, by-market-type, by-rationale-category, allocation calibration, drawdown series, balance series
- 11 new tests covering settled bets, losses, no bets, missing account, custom buckets

### Files Modified

- `alembic/env.py` — Added wagering model import
- `src/edgebook/core/money.py` — NEW: shared money utilities
- `src/edgebook/api/accounts.py` — Import from core/money, add reconciliation endpoint
- `src/edgebook/api/wagering.py` — Import from core/money, add rationale_category + notes
- `src/edgebook/api/cfb.py` — Add sport field, score correction endpoint
- `src/edgebook/api/analytics.py` — NEW: analytics endpoint and schemas
- `src/edgebook/cfb/models.py` — Add SportType enum, sport column, ScoreCorrection model
- `src/edgebook/cfb/services.py` — Normalize enums, add sport param, alternative line support
- `src/edgebook/ledger/services.py` — Add reconciliation + post_adjustment functions
- `src/edgebook/wagering/models.py` — Add RationaleCategory enum, rationale_category + notes fields
- `src/edgebook/wagering/services.py` — Add structured reasoning to place_bet, add correct_game_result
- `src/edgebook/analytics/__init__.py` — NEW
- `src/edgebook/analytics/services.py` — NEW: all analytics computation
- `src/edgebook/main.py` — Register analytics router
- `tests/api/test_accounts.py` — Add reconciliation test
- `tests/api/test_cfb.py` — Update for alternative lines, add multi-line test
- `tests/api/test_wagering.py` — Add structured reasoning + score correction tests
- `tests/api/test_analytics.py` — NEW: 11 analytics tests
- `docs/implementation_schedule.md` — Phase 2 and 3 marked complete with task tables
- `docs/api/openapi.yaml` — Added analytics, reconciliation, correction endpoints
- `docs/data/contracts.md` — Added sport, ScoreCorrection, CFB Market contracts
- `docs/architecture/adr/adr-0001-initial-architecture.md` — Filled with modular monolith ADR
- `docs/architecture/data_modeling.md` — Filled with data modeling guide
- `.agent/CONTEXT.md` — Updated to Phase 4 planning

### Migrations Added

- `alembic/versions/20260711_03_structured_reasoning_fields.py`
- `alembic/versions/20260711_04_alternative_market_lines.py`
- `alembic/versions/20260711_05_score_correction.py`
- `alembic/versions/20260711_06_sport_column.py`

### Commands Run
```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/ --ignore-missing-imports
uv run pytest -q
```

## Verification

- Ruff formatting: 48 files formatted, all clean
- Ruff linting: All checks passed
- Mypy: Success, no issues found in 24 source files
- Pytest: 47 passed (18 new tests since last commit), 90.80% coverage
- All migrations tested via test fixture (upgrade to head)

## Decisions Made

- **Structured reasoning**: `rationale_category` enum + `notes` field; kept legacy `reason` for backward compatibility
- **Alternative lines**: Dropped DB unique constraint; service layer enforces one moneyline per game and unique spread/total per line
- **Score correction**: Full audit trail via offsetting ADJUSTMENT entries — no deletions, preserves append-only invariant
- **Sharpe ratio**: Uses population std dev of per-bet returns; null for < 2 bets
- **Drawdown**: Computed per-ledger-transaction (includes stake debits as drawdown events)
- **Allocation buckets**: Default `[1, 2, 5, 10, 25]`; configurable via query param
- **Sport column**: Added to `cfb_games` with default `"CFB"` for multi-sport future-proofing
- **Parlays/teasers**: Deferred to after Phase 4 (need real market odds)

## Issues Encountered

- Reconciliation initially double-counted starting bankroll (added it to sum of postings); fixed by computing balance as just the sum of postings since the opening deposit is already a posting
- Test helper `create_open_market` used hardcoded team names, causing 409 conflicts when called multiple times in the same test; fixed by generating unique team name suffixes in the analytics test helper
- Max drawdown test assertion was wrong — drawdown correctly includes stake debits as temporary balance reductions

## Next Steps

1. Review and commit all work on `feat/manual-betting-flow`
2. Optionally push and open a pull request
3. Plan Phase 4: External Ingestion (CFB API integration for automated game/schedule/score data)

## Handoff Notes

- **Current state**: Phases 0, 1, 2, and 3 are complete and locally verified. All work is uncommitted on `feat/manual-betting-flow`.
- **Files to review first**: `src/edgebook/analytics/services.py`, `src/edgebook/api/analytics.py`, `src/edgebook/wagering/services.py` (correct_game_result)
- **Blockers**: None
- **Next priority**: Phase 4 External Ingestion planning
- **Open questions**: Which CFB data API to use for external ingestion? What rate limits apply? How to handle automated settlement scheduling?
- **Dependencies**: No external services or real-money integrations
- **Technical debt**: `utils/logging.py` has 37% coverage (pre-existing); `core/money.py` at 72% (validation edge cases not exercised)

---

**Session Owner**: OpenCode (glm-5.2)
**User**: Connor Kitchings
