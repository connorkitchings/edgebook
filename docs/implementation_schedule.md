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

### Phase 2: Product Hardening ☐ NOT STARTED
- Enforce double-entry ledger controls.
- Expand support for teasers/parlays and alternative market lines.
- Implement structured reasoning fields.

### Phase 3: Analytics ☐ NOT STARTED
- Calculate ROI, win-loss units, and bankroll drawdowns.
- Stake-allocation calibration chart logic.

### Phase 4: External Ingestion ☐ NOT STARTED
- CFB API integration to ingest games, schedules, and scores.
- Automated bet settlement tasks.

### Phase 5: AI-Assisted Review ☐ NOT STARTED
- Automated review of betting rationale and cognitive bias detection.

### Phase 6: Investment Adaptability Review ☐ NOT STARTED
- Architecture audit of separation between ledger, CFB, and wagering boundaries.
