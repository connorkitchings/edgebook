# Runbook: Edgebook

This runbook documents how to run, test, and troubleshoot the Edgebook college football paper-betting platform local environment.

## Getting Started

> **Hosting:** see [Deployment](deployment.md) for the full Oracle Always-Free
> walkthrough (VM provisioning, secrets, cron ingestion, CI/CD, and the HTTPS
> upgrade path).

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

## Backups

The production stack stores data in the `pgdata` Docker volume backing the
Postgres service in `docker-compose.prod.yml`. `scripts/backup_db.sh` and
`scripts/restore_db.sh` dump and restore that database through the running `db`
service, so the stack must be up when either script is executed.

### Back up

```bash
# Default: dump via docker-compose.prod.yml into ./backups, keep the 7 newest.
scripts/backup_db.sh

# Override the compose target or retention:
COMPOSE_FILE=docker-compose.yml RETENTION=14 scripts/backup_db.sh
```

Backups are written as compressed `pg_dump` custom-format files named
`edgebook-<UTC-timestamp>.dump` under `./backups/` (git-ignored). Only the
`RETENTION` most recent files are retained; older backups are pruned
automatically.

### Restore

```bash
scripts/restore_db.sh backups/edgebook-20260712T180000Z.dump
```

Restore drops and recreates the `public` schema, then loads the backup with
`pg_restore --no-owner --no-acl`. To guard against accidental production
overwrites, the script prompts you to type the target database name before
proceeding.

### Scheduled backups

On the production host, run a daily backup via cron shortly before any intake
or maintenance jobs:

```cron
15 8 * * *  cd /opt/edgebook && ./scripts/backup_db.sh >> logs/backup.log 2>&1
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

The production pregame worker runs once daily at 08:00 America/New_York and requests the
DraftKings, FanDuel, BetMGM, and Caesars featured markets (`h2h`, `spreads`, and `totals`). It
is a separate Docker service, not part of the FastAPI process. Ingestion runs record the requested
and provider snapshot times plus remaining provider quota.

Historical backfills request one daily 12:00 UTC snapshot at a time. Each request receives a
durable checkpoint keyed by provider, sport, markets, bookmaker set, and requested timestamp;
rerunning the same range skips completed days and resumes failed ones. Start the full research
load at the provider's supported date (`2020-06-06`) only after a small three-day smoke backfill.
The worker stops future requests once the configured `INGESTION_MIN_QUOTA_REMAINING` reserve is
reached.

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

## Ingestion Alerting

Operator visibility into ingestion health is surfaced in three layers.

### In-app

The `/ingestion` page renders a run-health summary card (last 24h by default),
per-provider quota, and a filterable run-history table. Failed runs show a red
badge plus the error message inline; `status` and `provider` filters narrow the
history. The `/ingestion/runs` and `/ingestion/runs/summary` JSON endpoints
back the same data for automation.

### Webhook notifier

Set `ALERT_WEBHOOK_URL` to `POST` a JSON alert whenever an ingestion run fails
(best-effort, one-shot — there is no retry queue):

```json
{
  "event": "ingestion.run_failed",
  "run_id": "...",
  "provider": "the-odds-api",
  "scope": "games",
  "error": "ValueError: ...",
  "started_at": "2026-07-13T12:00:00+00:00",
  "quota_remaining": 123,
  "notified_at": "2026-07-13T12:00:05+00:00"
}
```

Delivery uses a bounded timeout (`ALERT_WEBHOOK_TIMEOUT_SECONDS`, default 5) and
swallows transport errors, so alerting can never break ingestion. Leave
`ALERT_WEBHOOK_URL` empty to disable. The payload contains no credentials.

### Prometheus metrics

The `/metrics` endpoint (see Phase 8.3) exports ingestion signals suitable for
alert rules:

- `edgebook_ingestion_runs_total{provider,scope,status}` — counter; alert on a
  non-zero failed-run rate, e.g.
  `sum(increase(edgebook_ingestion_runs_total{status="FAILED"}[15m])) > 0`.
- `edgebook_ingestion_quota_remaining{provider}` — gauge; alert when a provider
  nears its reserve, e.g.
  `edgebook_ingestion_quota_remaining{provider="the-odds-api"} < 100`.

---

## Releases

The canonical version lives in `pyproject.toml`; `edgebook.__version__` and the
FastAPI app version read it at runtime via `importlib.metadata`, so bumping the
`pyproject.toml` version updates everything. The full pre-release checklist
lives in `.agent/workflows/release-checklist.md`; the routine cut-a-tag flow is:

1. Update the version in `pyproject.toml`.
2. Move `[Unreleased]` notes into a dated section in `CHANGELOG.md` and add a
   new empty `[Unreleased]` heading.
3. `uv sync` (so the installed metadata reflects the new version), then run the
   full quality gate: `uv run ruff format . && uv run ruff check . &&
   uv run pytest`.
4. Commit, tag, and push:

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: release vX.Y.Z"
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin main --tags
   ```

The production deploy workflow is pending a hosting-target decision; until then,
a release is a versioned git tag plus the published container image build.

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
