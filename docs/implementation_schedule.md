# Edgebook - Implementation Schedule

This schedule tracks the progress of the Edgebook simulation platform development phases.

**Status Legend:** ☐ Not Started · ▶ In Progress · ✅ Done · ⚠ Risk/Blocked

---

## Roadmap Overview

### Phase 0: Project Foundation (THIS SESSION) ✅ COMPLETE
Initialize the python environment, database configurations, and testing foundations.

| Phase | Task | Deliverable | Status | Notes |
|-------|------|-------------|--------|-------|
| 0.1 | Rename python package to edgebook | Package folder renamed to `edgebook` | ✅ Done | Completed |
| 0.2 | Pin python version and setup uv | `.python-version` pinned to 3.11 | ✅ Done | Completed |
| 0.3 | Add FastAPI, Pydantic, SQLAlchemy | Virtual environment synced with dependencies | ✅ Done | Completed |
| 0.4 | Implement core database session setup | `src/edgebook/core/database.py` created | ✅ Done | Completed |
| 0.5 | Setup initial FastAPI app & health check | `src/edgebook/main.py` created | ✅ Done | Completed |
| 0.6 | Establish tests and pass health check | 53 unit tests passing successfully | ✅ Done | Completed |
| 0.7 | Update documentation | Project charter, brief, schedules updated | ✅ Done | Completed |

---

## Upcoming Phases

### Phase 1: Manual End-to-End Betting Flow ✅ COMPLETE
Implement manual creation of fictional accounts, game data entry, bet placement, score recording, and automated ledger adjustments.

| Phase | Task | Deliverable | Status | Notes |
|-------|------|-------------|--------|-------|
| 1.1 | Fictional Account Creation | Generic double-entry ledger, account API, and statement history | ✅ Done | Includes Alembic schema and append-only ledger records. |
| 1.2 | Manual Game & Odds Input | Team catalog plus manual game, market, and American-odds intake APIs | ✅ Done | CFB module remains isolated from the ledger. |
| 1.3 | Place Simulated Bet | Record stake, locked odds, bankroll snapshot, and optional reason | ✅ Done | Conviction is derived from stake relative to pre-bet bankroll. |
| 1.4 | Settlement Engine | Evaluate final scores and credit ledger | ✅ Done | Atomic win/loss/push settlement with immutable payout postings. |
| 1.5 | Bet History View | Display statements and past bets | ✅ Done | Paginated account history and bet detail APIs. |

---

### Phase 2: Product Hardening ✅ COMPLETE
Strengthen ledger integrity, add structured reasoning for analytics, support alternative market lines, and implement score correction workflows with full audit trails.

#### Phase 2A: Ledger Hardening & Structured Reasoning

| Task | Deliverable | Status | Notes |
|------|-------------|--------|-------|
| Add reconciliation service | `reconcile_account_balance()` verifies materialized balance | ✅ Done | Compares `current_balance_cents` to sum of postings |
| Add reconciliation API endpoint | `POST /accounts/{id}/reconcile` | ✅ Done | Returns balance status and discrepancy if any |
| Add `rationale_category` enum to Bet model | Typed rationale field (nullable) | ✅ Done | Categories: MATCHUP_ANALYSIS, STATISTICAL_EDGE, LINE_VALUE, INJURY_IMPACT, SITUATIONAL, CONTRARIAN, OTHER |
| Add `notes` field to Bet model | Backward-compatible with legacy `reason` | ✅ Done | Both fields coexist; new bets use `notes` |
| Update API schemas for reasoning | Accept/return `rationale_category` and `notes` | ✅ Done | BetCreate and BetResponse updated |

#### Phase 2B: Alternative Market Lines

| Task | Deliverable | Status | Notes |
|------|-------------|--------|-------|
| Relax market uniqueness constraint | Dropped `UNIQUE(game_id, market_type)` | ✅ Done | Service layer enforces: one moneyline per game; spread/total unique per line |
| Update market creation service | Allow multiple spread/total markets with different lines | ✅ Done | Duplicate line still rejected with 409 |
| Update tests | Verify alternative lines and duplicate detection | ✅ Done | New test for multi-line betting flow |

#### Phase 2C: Score Correction Workflow

| Task | Deliverable | Status | Notes |
|------|-------------|--------|-------|
| Add `ScoreCorrection` model | Track original/corrected scores with reason | ✅ Done | Table: `cfb_score_corrections` |
| Implement score correction service | `correct_game_result()` with full audit trail | ✅ Done | Offsetting ADJUSTMENT entries reverse payouts; re-settlement creates new WAGER_PAYOUT entries |
| Add correction API endpoint | `PUT /cfb/games/{id}/correction` | ✅ Done | Local simulation endpoint; authorization required before external exposure |
| Preserve append-only invariant | All corrections via offsetting entries | ✅ Done | No deletions; original payouts and reversals remain in ledger |

#### Deferred to Later Phases

| Feature | Reason | Target Phase |
|---------|--------|--------------|
| Parlays | Requires real market odds data | After Phase 4 (External Ingestion) |
| Teasers | Complex line adjustment logic; needs real odds | After Phase 4 (External Ingestion) |
| Authentication | Not required for the local simulation workflow; required before external exposure | Before public deployment |

### Phase 3: Analytics ✅ COMPLETE
Calculate ROI, win-loss units, bankroll drawdowns, stake-allocation calibration, Sharpe ratio, and analytics by rationale category, sport, and market type.

| Task | Deliverable | Status | Notes |
|------|-------------|--------|-------|
| Add `sport` column to `cfb_games` | Migration, model, API update; defaults to `"CFB"` | ✅ Done | Future-proofs analytics for multi-sport expansion |
| Summary metrics service | ROI, win rate, net profit, Sharpe ratio, max drawdown | ✅ Done | Sharpe uses per-bet returns with population std dev |
| Per-sport breakdown | GROUP BY `cfb_games.sport` | ✅ Done | Currently only CFB; ready for expansion |
| Per-market-type breakdown | GROUP BY `bet.market_type` | ✅ Done | SPREAD, MONEYLINE, TOTAL |
| Per-rationale-category breakdown | GROUP BY `bet.rationale_category` | ✅ Done | Null category grouped explicitly |
| Allocation calibration | Bucket by conviction %, configurable boundaries | ✅ Done | Default buckets: <1%, 1-2%, 2-5%, 5-10%, 10-25%, 25%+ |
| Drawdown series | Per-transaction drawdown from chronological replay | ✅ Done | Chart-ready: timestamp, balance, peak, drawdown_pct, event |
| Balance series | Daily balance from transaction replay | ✅ Done | Chart-ready: date, balance |
| API endpoint + schemas | `GET /accounts/{id}/analytics` with date range and bucket params | ✅ Done | All params optional; ranges require timezone-aware bounds and valid bucket boundaries |
| Tests | 11 tests covering settled bets, losses, no bets, missing account, custom buckets | ✅ Done | 47 total tests, 90.80% coverage |

### Phase 4: Multi-Source External Ingestion ✅ COMPLETE
- Provider-neutral normalized-feed adapters, provenance records, source-specific odds, score-conflict holds, and scheduler-safe commands are implemented.
- The Odds API is implemented as the credentialed NCAAF provider for bookmaker-specific current and historical snapshots. SportsDataIO and CollegeFootballData adapters are fixture-ready pending approved credentials and terms.
- **Deferred:** Production provider adapters, credentials, and source terms for at least three independent providers require key provisioning before live ingestion is ready.

### Phase 5: Rationale Review Workflow ✅ COMPLETE
- Asynchronous human-review tasks, local completion APIs, an operator queue with atomic claims, review coverage, and bias-tag analytics are implemented.
- Added `/reviews/{bet_id}` and `/reviews/{bet_id}/complete` endpoints with JSON and HTML responses.
- Review card partial renders inline with HTMX claim/complete forms; status badges use consistent `status_label` filter.
- Operator protection: only the claiming reviewer can complete a review.
- Model execution remains deliberately deferred behind the review workflow boundary.

### Phase 6: Investment Adaptability Review ☐ NOT STARTED
- Architecture audit of separation between ledger, CFB, and wagering boundaries.
