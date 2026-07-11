# Data Contracts

This document outlines the data contracts for Edgebook's core data assets. Each contract
defines the schema, quality expectations, and ownership of the data. All balances are
fictional simulation credits.

## Table of Contents

- [Ledger Account](#ledger-account)
- [Ledger Transaction](#ledger-transaction)
- [CFB Game](#cfb-game)
- [CFB Market Quote](#cfb-market-quote)

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
    "scheduled_at": {"type": "string", "format": "date-time"},
    "status": {"type": "string", "enum": ["SCHEDULED"]},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "home_team_id", "away_team_id", "scheduled_at"]
}
```

### Quality Expectations
- **Integrity:** `home_team_id != away_team_id` (enforced by check constraint).

### Ownership
- **Owner:** Edgebook CFB module (`src/edgebook/cfb/`)

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
