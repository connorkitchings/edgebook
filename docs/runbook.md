# Runbook: Edgebook

This runbook documents how to run, test, and troubleshoot the Edgebook college football paper-betting platform local environment.

## Getting Started

### 1. Prerequisites
- **Python 3.11**: Ensure you have Python 3.11 installed.
- **uv**: Project package manager. Install via `pip install uv`.

### 2. Development Setup
To prepare your environment, follow these steps:

```bash
# Clone the repository
git clone <repository-url>
cd edgebook

# Force Python version pinning (created automatically)
uv python pin 3.11

# Install dependencies (including dev)
uv sync

# Run tests to verify setup
uv run pytest
```

### 3. Apply Database Migrations

Edgebook manages its schema through Alembic; application startup never creates
tables automatically. Apply the current revision before using account or CFB
intake endpoints:

```bash
uv run alembic upgrade head
```

### 3. Running the Server
To start the FastAPI development server:

```bash
uv run uvicorn edgebook.main:app --reload
```

The application will be running at `http://127.0.0.1:8000`.
You can access the interactive API docs at `http://127.0.0.1:8000/docs`.

---

## Service Verification & Health Checks

### Check API Status
Run the following curl command:

```bash
curl http://127.0.0.1:8000/health
```

**Expected Response (SQLAlchemy connected to database):**
```json
{
  "status": "ok",
  "services": {
    "api": "ok",
    "database": "ok"
  }
}
```

## Ingestion Scheduler Hooks

The ingestion worker is intentionally outside the FastAPI process. The Odds API is the supported
credentialed provider for current and historical NCAAF featured markets; SportsDataIO and
CollegeFootballData adapters are fixture-ready until their terms and credentials are approved.
Configure secrets only through the environment, never a feed file or source control.

```bash
ODDS_API_KEY=... uv run python -m edgebook.ingestion.cli providers
ODDS_API_KEY=... uv run python -m edgebook.ingestion.cli sync --provider the-odds-api
ODDS_API_KEY=... uv run python -m edgebook.ingestion.cli backfill-odds \
  --provider the-odds-api --from 2026-09-01 --to 2026-09-07
ODDS_API_KEY=... uv run python scripts/odds_api_smoke.py
# Requires historical-data entitlement:
ODDS_API_KEY=... uv run python scripts/odds_api_smoke.py --historical-date 2025-09-01
```

The conservative research schedule is one current sync per day outside game week, hourly during
game week, and every 10 minutes in the six pregame hours. Historical backfills request one daily
snapshot at a time and can safely be rerun because provider observations are immutable and
idempotent.

Fixture and settlement commands remain available:

```bash
uv run python -m edgebook.ingestion.cli sync --provider provider-a --feed provider-a.json
uv run python -m edgebook.ingestion.cli settle-confirmed
uv run python -m edgebook.ingestion.cli claim-reviews
uv run python -m edgebook.ingestion.cli report
```

Score disagreements remain held in `CONFLICTED` state and must be resolved through the local
score-resolution API before settlement.

---

## Troubleshooting

### Issue: PyO3 Compilation Error on Python 3.14+
**Symptoms:**
Installing dependencies via `uv sync` crashes during `pydantic-core` build with the message:
`error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version (3.13)`

**Resolution:**
Edgebook requires Python 3.11/3.12. Ensure you run:
```bash
uv python pin 3.11
rm -rf .venv
uv sync
```
This forces `uv` to use Python 3.11.

### Issue: Database connectivity down
**Symptoms:**
`/health` response returns database as "down" or "unhealthy".

**Resolution:**
1. Check that the file `edgebook.db` is present in the root directory (for SQLite).
2. If `DATABASE_URL` is customized in `.env` to target a PostgreSQL database, verify that the database server is running and the credentials are correct.
