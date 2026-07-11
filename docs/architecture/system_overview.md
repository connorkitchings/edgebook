# System Overview

This document provides a high-level overview of the Edgebook architecture. Edgebook is a
**simulation-only college football paper-betting platform** built as a modular monolith.

## Architecture Diagram

```mermaid
graph TD
    subgraph "Clients"
        A[API Consumer]
    end

    subgraph "Application - FastAPI modular monolith"
        B[API Layer<br/>src/edgebook/api]
        C[CFB Domain<br/>src/edgebook/cfb]
        D[Ledger Domain<br/>src/edgebook/ledger]
        E[Core<br/>config + database session]
    end

    subgraph "Persistence"
        F[(PostgreSQL<br/>SQLite for local dev)]
        G[Alembic migrations]
    end

    A -->|HTTP REST| B
    B --> C
    B --> D
    B --> E
    C --> E
    D --> E
    E --> F
    G -->|schema| F
```

## Core Design Principle: Strict Module Separation

The ledger accounting module (`src/edgebook/ledger/`) is **strictly isolated** from the
college-football domain module (`src/edgebook/cfb/`). The two never import from each other
directly. This keeps the double-entry ledger reusable for future paper-investing use cases
beyond sports betting, and confines CFB-specific rules to their own boundary.

The API layer (`src/edgebook/api/`) is the only place that orchestrates across both modules.

## Components

### API Layer (`src/edgebook/api/`)
- **`accounts.py`** — Fictional account creation, deposits/withdrawals, and statement history.
- **`cfb.py`** — Manual intake of teams, games, markets, and American-odds quotes.
- FastAPI provides automatic request validation and OpenAPI docs at `/docs`.

### CFB Domain (`src/edgebook/cfb/`)
- **Models:** `Team`, `Game`, `Market`, `MarketQuote`.
- **Markets:** Spread, Moneyline, and Total with `HOME`/`AWAY`/`OVER`/`UNDER` selections.
- **Intake:** Manual entry only in Phase 1; external ingestion is a later phase.
- CFB intake never touches ledger balances.

### Ledger Domain (`src/edgebook/ledger/`)
- **Models:** `Account`, `JournalEntry`, `Transaction`.
- **Double-entry:** Every balance change is a balanced set of signed postings between the
  user's `USER_ASSET` account and the internal `EQUITY` (simulation-capital) counterparty.
- **Immutable & append-only:** Postings and journal entries are never mutated.
- **Transaction types:** `DEPOSIT`, `WITHDRAWAL`, `WAGER_STAKE`, `WAGER_PAYOUT`, `ADJUSTMENT`.

### Core (`src/edgebook/core/`)
- **`config.py`** — Pydantic `Settings` (project name, database URL, etc.).
- **`database.py`** — SQLAlchemy session/engine setup and `get_db` dependency.

### Persistence
- **PostgreSQL 15+** is the system of record for production.
- **SQLite** is used for local development and the test suite.
- **Alembic** manages schema migrations (`alembic/versions/`).

## Money Representation

All monetary amounts are stored as **integer cents** (`_cents` columns) to avoid
floating-point rounding. The API accepts two-decimal floats and converts internally.

## Roadmap Context

This overview reflects Phase 1 (manual end-to-end betting flow). Future phases add automated
settlement, analytics, external CFB ingestion, and AI-assisted review. See the
[Implementation Schedule](../implementation_schedule.md) for the full roadmap.
