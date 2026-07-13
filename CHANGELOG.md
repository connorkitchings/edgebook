# Changelog

All notable changes to Edgebook are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Accumulated platform work since the initial foundation release; not yet tagged.

### Added

- **Wagering:** manual bet placement with locked odds (conviction derived from
  stake-to-bankroll), alternative market lines (spreads/totals/moneyline),
  score-correction workflow with audit trail, and paginated bet history.
- **CFB module:** structured rationale categories, isolated from the ledger
  domain.
- **Analytics:** ROI, win rate, Sharpe ratio, max drawdown, allocation
  calibration, and chart-ready balance/drawdown series by sport, market, and
  rationale.
- **Ingestion:** provider-neutral adapters with provenance; The Odds API as the
  credentialed NCAAF provider for current and historical snapshots; durable
  backfill checkpoints and quota-aware runs; scheduler-safe commands.
- **Review workflow:** asynchronous operator queue with atomic claims, review
  coverage, and bias-tag analytics.
- **Auth:** JWT auth, role-based access (USER/OPERATOR/ADMIN), login/register
  pages, and protected correction/review workflows.
- **Frontend:** HTMX-driven dashboard, analytics, games, bets, reviews, and
  ingestion pages.
- **Observability:** Prometheus `/metrics`, liveness/readiness probes
  (`/healthz`, `/readyz`), HTTP and ingestion-run metrics, and a best-effort
  failure webhook notifier.
- **Operations:** production settings hardening, Postgres backup/restore
  scripts with retention, an operator ingestion dashboard (summary, filters,
  failure surfacing), and structured JSON production logging.

### Changed

- Application orchestration boundary refactored out of the ingestion domain,
  with AST-enforced import rules (ADR-0002).

### Security

- Production `SECRET_KEY` validation rejects default/empty/short keys at
  startup.
- Provider credentials are read only from the environment, never the feed file
  or version control.

## [0.1.0] - 2026-07-10

### Added

- **FastAPI application** (`src/edgebook/main.py`) with health-check endpoint.
- **Core infrastructure** — Pydantic settings (`core/config.py`) and SQLAlchemy session setup (`core/database.py`).
- **Double-entry ledger** — account creation, immutable postings, and statement history (`src/edgebook/ledger/`).
- **CFB domain module** — team catalog plus manual game, market, and American-odds intake (`src/edgebook/cfb/`).
- **REST API** — fictional accounts and ledger transactions (`api/accounts.py`), CFB intake (`api/cfb.py`).
- **Alembic migrations** — initial schema for ledger and CFB models.
- **Test suite** — unit and API tests covering config, database, migrations, accounts, CFB, and ledger services.
- **Project documentation** — charter, brief, implementation schedule, runbook, and security policy.
- **Tooling** — Ruff format/lint, pytest with coverage, pre-commit hooks, and a Makefile.

### Project Foundation

- Pinned Python to 3.11 (`.python-version`) to resolve Pydantic core compilation issues under 3.14.
- Adopted a modular monolith architecture with strict separation between the `ledger` and `cfb` modules.

## Versioning

The canonical version lives in `pyproject.toml` and is read at runtime via
`importlib.metadata`; `edgebook.__version__` and the FastAPI app version follow
automatically. See the runbook's Releases section for the tagging flow.
