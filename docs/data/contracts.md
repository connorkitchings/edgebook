# Data Contracts

This document outlines the data contracts for Edgebook's core data assets. Each contract
defines the schema, quality expectations, and ownership of the data. All balances are
fictional simulation credits.

## Table of Contents

- [Ledger Account](#ledger-account)
- [Ledger Transaction](#ledger-transaction)
- [CFB Game](#cfb-game)
- [CFB Market](#cfb-market)
- [CFB Market Quote](#cfb-market-quote)
- [Simulated Bet](#simulated-bet)
- [Score Correction](#score-correction)
- [Provider Observation](#provider-observation)
- [Bet Review](#bet-review)

---

## Ledger Account

### Description
A generic ledger account holding a materialized simulation-credit balance, owned by a user.
Separate from any sportsbook concept so the ledger can be reused for other paper-investing
use cases.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid", "description": "Primary key (UUID string)"},
    "owner_name": {"type": "string", "maxLength": 200},
    "kind": {"type": "string", "enum": ["USER_ASSET", "EQUITY"]},
    "is_active": {"type": "boolean"},
    "starting_bankroll_cents": {"type": "integer", "minimum": 0},
    "current_balance_cents": {"type": "integer"},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "owner_name", "kind", "starting_bankroll_cents", "current_balance_cents"]
}
```

### Quality Expectations
- **Completeness:** `owner_name` always populated; `starting_bankroll_cents >= 0`.
- **Accuracy:** `current_balance_cents` must equal the sum of signed transaction postings.
- **Uniqueness:** `id` is unique.

### Ownership
- **Owner:** Edgebook ledger module (`src/edgebook/ledger/`)

---

## Ledger Transaction

### Description
An immutable, signed posting within a balanced journal entry. Postings are append-only and
never mutated.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "journal_entry_id": {"type": "string", "description": "FK to balanced journal entry"},
    "account_id": {"type": "string", "description": "FK to ledger account"},
    "transaction_type": {
      "type": "string",
      "enum": ["DEPOSIT", "WITHDRAWAL", "WAGER_STAKE", "WAGER_PAYOUT", "ADJUSTMENT"]
    },
    "amount_cents": {"type": "integer", "description": "Signed, non-zero"},
    "description": {"type": ["string", "null"]},
    "created_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "journal_entry_id", "account_id", "transaction_type", "amount_cents"]
}
```

### Quality Expectations
- **Integrity:** `amount_cents != 0`; journal entries must balance to zero across postings.
- **Immutability:** Once written, rows are never updated or deleted.

### Ownership
- **Owner:** Edgebook ledger module (`src/edgebook/ledger/`)

---

## CFB Game

### Description
A scheduled college-football contest between two distinct teams.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "home_team_id": {"type": "string", "description": "FK to cfb_teams"},
    "away_team_id": {"type": "string", "description": "FK to cfb_teams"},
    "sport": {"type": "string", "enum": ["CFB"], "description": "Sport category (defaults to CFB)"},
    "scheduled_at": {"type": "string", "format": "date-time"},
    "status": {"type": "string", "enum": ["SCHEDULED", "FINAL"]},
    "home_score": {"type": ["integer", "null"], "minimum": 0},
    "away_score": {"type": ["integer", "null"], "minimum": 0},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "home_team_id", "away_team_id", "scheduled_at"]
}
```

### Quality Expectations
- **Integrity:** `home_team_id != away_team_id` (enforced by check constraint).
- **Finality:** A `FINAL` game has both scores. Scores can be corrected via the score-correction workflow (Phase 2C), which creates offsetting ledger entries and an audit record.

### Ownership
- **Owner:** Edgebook CFB module (`src/edgebook/cfb/`)

---

## Provider Observation

### Description
An immutable normalized record from one external provider. Observations retain raw provenance and
are never collapsed into a canonical odds line.

### Quality Expectations
- **Idempotency:** Provider, scope, external ID, and payload hash uniquely identify a replay.
- **Provenance:** Every imported game, quote, and score links to a provider observation.
- **Scores:** Disagreeing final-score observations hold the game in `CONFLICTED` state.

### Ownership
- **Owner:** Edgebook ingestion module (`src/edgebook/ingestion/`)

---

## Bet Review

### Description
An asynchronous, human-operated review task linked one-to-one with a simulated bet rationale.

### Quality Expectations
- **Lifecycle:** `PENDING`, `IN_REVIEW`, `COMPLETED`, `FAILED`, or `NOT_APPLICABLE`.
- **Isolation:** Review outcomes never modify odds, settlements, balances, or financial analytics.
- **Future compatibility:** The review version identifies the human or future model workflow.

### Ownership
- **Owner:** Edgebook wagering module (`src/edgebook/wagering/`)

---

## CFB Market

### Description
A manual market line for one game and market type. Multiple markets of the same type may
exist for a game when they have different lines (alternate spreads/totals). Moneyline is
limited to one per game.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "game_id": {"type": "string", "description": "FK to cfb_games"},
    "market_type": {"type": "string", "enum": ["SPREAD", "MONEYLINE", "TOTAL"]},
    "line_millipoints": {"type": ["integer", "null"], "description": "Point line in millipoints (null for moneyline)"},
    "status": {"type": "string", "enum": ["DRAFT", "OPEN"]},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "game_id", "market_type", "status"]
}
```

### Quality Expectations
- **Uniqueness:** One moneyline per game; spread/total unique per `(game_id, market_type, line_millipoints)`.
- **Lifecycle:** Markets start as DRAFT and transition to OPEN when required quotes are present.

---

## Simulated Bet

### Description
A straight paper bet that links a fictional account to a CFB quote while preserving the
exact placement terms and ledger audit references.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "account_id": {"type": "string"},
    "game_id": {"type": "string"},
    "market_id": {"type": "string"},
    "quote_id": {"type": "string"},
    "selection": {"type": "string", "enum": ["HOME", "AWAY", "OVER", "UNDER"]},
    "market_type": {"type": "string", "enum": ["SPREAD", "MONEYLINE", "TOTAL"]},
    "line_millipoints": {"type": ["integer", "null"]},
    "american_odds": {"type": "integer"},
    "stake_cents": {"type": "integer", "minimum": 1},
    "bankroll_before_cents": {"type": "integer", "minimum": 1},
    "payout_cents": {"type": ["integer", "null"], "minimum": 0},
    "reason": {"type": ["string", "null"], "maxLength": 500, "description": "Legacy free-text rationale"},
    "rationale_category": {
      "type": ["string", "null"],
      "enum": ["MATCHUP_ANALYSIS", "STATISTICAL_EDGE", "LINE_VALUE", "INJURY_IMPACT", "SITUATIONAL", "CONTRARIAN", "OTHER", null]
    },
    "notes": {"type": ["string", "null"], "maxLength": 500, "description": "Structured free-text notes (Phase 2)"},
    "status": {"type": "string", "enum": ["PENDING", "WON", "LOST", "PUSH"]}
  },
  "required": ["id", "account_id", "game_id", "market_id", "selection", "american_odds", "stake_cents", "bankroll_before_cents", "status"]
}
```

### Quality Expectations
- **Atomicity:** Creation and stake posting succeed or fail together; settlement and payout do likewise.
- **Snapshot integrity:** Odds, line, stake, and placement bankroll never follow later market/account changes.
- **Allocation:** Conviction is derived as `stake_cents / bankroll_before_cents`.

### Ownership
- **Owner:** Edgebook wagering module (`src/edgebook/wagering/`)

---

## CFB Market Quote

### Description
A single manual American-odds quote for one selection within a market. A market opens once it
has its required pair of quotes.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "market_id": {"type": "string", "description": "FK to cfb_markets"},
    "selection": {"type": "string", "enum": ["HOME", "AWAY", "OVER", "UNDER"]},
    "american_odds": {"type": "integer", "description": "Signed American odds"},
    "created_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "market_id", "selection", "american_odds"]
}
```

### Quality Expectations
- **Uniqueness:** One quote per `(market_id, selection)` pair.
- **Accuracy:** `american_odds` is a non-zero signed integer.

### Ownership
- **Owner:** Edgebook CFB module (`src/edgebook/cfb/`)

---

## Score Correction

### Description
An audit-trail record for a corrected final score. Each correction stores the original and
corrected scores along with a required reason. The correction process reverses prior payout
postings via offsetting ADJUSTMENT entries and re-settles all bets atomically.

### Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "game_id": {"type": "string", "description": "FK to cfb_games"},
    "original_home_score": {"type": "integer", "minimum": 0},
    "original_away_score": {"type": "integer", "minimum": 0},
    "corrected_home_score": {"type": "integer", "minimum": 0},
    "corrected_away_score": {"type": "integer", "minimum": 0},
    "reason": {"type": "string", "maxLength": 1000},
    "corrected_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "game_id", "original_home_score", "original_away_score", "corrected_home_score", "corrected_away_score", "reason", "corrected_at"]
}
```

### Quality Expectations
- **Integrity:** `corrected_scores != original_scores`; game must be FINAL at correction time.
- **Audit trail:** Offsetting ADJUSTMENT entries preserve the append-only ledger invariant.
- **Immutability:** Correction records are never updated or deleted.

### Ownership
- **Owner:** Edgebook CFB module (`src/edgebook/cfb/`)
