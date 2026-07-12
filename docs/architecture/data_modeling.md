# Data Modeling Guide

## Overview
Edgebook uses PostgreSQL (SQLite for local development) with SQLAlchemy 2.0 ORM. All monetary values are stored as integer cents. All primary keys are UUIDs. All timestamps are timezone-aware UTC.

## Core Entities

### Ledger Boundary

**Account** (`ledger_accounts`)
- Represents a fictional simulation-credit account
- `kind`: `USER_ASSET` (user accounts) or `EQUITY` (system capital account)
- `current_balance_cents`: Materialized balance updated atomically with postings
- `starting_bankroll_cents`: Initial funding amount

**JournalEntry** (`ledger_journal_entries`)
- Groups balanced postings into a single atomic transaction
- Immutable and append-only (enforced by DB triggers)
- Every journal entry must have postings that sum to zero

**Transaction** (`ledger_transactions`)
- Individual posting within a journal entry
- `amount_cents`: Signed integer (positive = credit, negative = debit)
- `transaction_type`: `DEPOSIT`, `WITHDRAWAL`, `WAGER_STAKE`, `WAGER_PAYOUT`, `ADJUSTMENT`
- Immutable and append-only (enforced by DB triggers)

### CFB Boundary

**Team** (`cfb_teams`)
- Reusable team catalog entry
- `normalized_name`: Lowercased, whitespace-collapsed for uniqueness

**Game** (`cfb_games`)
- Scheduled contest between two teams
- `status`: `SCHEDULED` or `FINAL`
- `home_score`, `away_score`: Nullable until finalized
- CHECK constraint: `home_team_id != away_team_id`

**Market** (`cfb_markets`)
- Betting market for a game (SPREAD, MONEYLINE, TOTAL)
- `status`: `DRAFT` (incomplete) or `OPEN` (ready for bets)
- `line_millipoints`: Point line in millipoints (3 decimal places of precision)
- UNIQUE constraint: `(game_id, market_type)` — one market per type per game

**MarketQuote** (`cfb_market_quotes`)
- Odds for a specific selection within a market
- `selection`: `HOME`, `AWAY`, `OVER`, or `UNDER`
- `american_odds`: Signed integer with magnitude >= 100
- UNIQUE constraint: `(market_id, selection)` — one quote per selection per market
- Provider quotes retain `source`, `source_event_id`, `source_quote_id`, and `observed_at`; a
  quote is append-only so its source-specific history remains available for research.

### Ingestion Operations Boundary

**ProviderEventLink** (`ingestion_provider_event_links`)
- Maps a provider event identifier to one canonical CFB game and survives provider schedule changes.

**BackfillCheckpoint** (`ingestion_backfill_checkpoints`)
- Records completion or failure for one requested historical snapshot and makes backfills resumable.

**IngestionRun** (`ingestion_runs`)
- Stores source scope, requested/provider snapshot times, record counts, failure detail, and provider quota metadata.

### Wagering Boundary

**Bet** (`wagering_bets`)
- Simulated wager on a market selection
- Snapshots odds, line, stake, and bankroll at placement time
- `status`: `PENDING`, `WON`, `LOST`, or `PUSH`
- `stake_transaction_id`: Links to ledger posting debiting the stake
- `payout_transaction_id`: Links to ledger posting crediting the payout (nullable until settled)
- `bankroll_before_cents`: Pre-bet balance for conviction calculation
- `reason`: Optional free-text rationale (max 500 chars)

## Relationships

```
Account (1) ──< (N) Transaction
JournalEntry (1) ──< (N) Transaction

Team (1) ──< (N) Game (as home_team)
Team (1) ──< (N) Game (as away_team)
Game (1) ──< (N) Market
Market (1) ──< (N) MarketQuote

Account (1) ──< (N) Bet
Game (1) ──< (N) Bet
Market (1) ──< (N) Bet
MarketQuote (1) ──< (N) Bet
```

## Design Principles

1. **Integer cents for money**: Avoid floating-point rounding errors. API accepts 2-decimal decimals, converts to cents internally.

2. **Millipoints for lines**: Point spreads and totals stored as integer millipoints (e.g., -3.5 = -3500). Provides 3 decimal places of precision without floats.

3. **Append-only ledger**: Journal entries and transactions cannot be updated or deleted (enforced by DB triggers). Corrections create offsetting entries.

4. **Materialized balances**: `Account.current_balance_cents` is denormalized for performance. Updated atomically within the same transaction as postings. Reconciliation service verifies consistency.

5. **Snapshot immutability**: Bets snapshot odds, line, and bankroll at placement. Subsequent changes to markets or accounts do not affect placed bets.

6. **UUID primary keys**: All entities use UUIDs for global uniqueness and security (no sequential ID enumeration).

7. **Timezone-aware timestamps**: All datetime columns use `DateTime(timezone=True)`. Stored in UTC, displayed in ISO 8601 format.

## Migrations
Alembic manages schema migrations. All model modules are imported in `alembic/env.py` to enable autogenerate detection. Migration files are in `alembic/versions/`.

## Constraints & Validation
- CHECK constraints enforce domain invariants at the database level
- FOREIGN KEY constraints with ON DELETE RESTRICT prevent orphaned records
- UNIQUE constraints prevent duplicate entries
- Service layer validates business rules before database operations
