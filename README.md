# Edgebook

> **A simulation-only college football paper-betting platform.** Manage a fictional bankroll, record simulated wagers, settle bets against final scores, and analyze allocation performance — with zero real-money risk.

---

## What Edgebook Provides

- **Double-entry ledger** — Immutable, audit-proof fictional bankroll with account creation, postings, and statement history.
- **CFB betting simulation** — Manual intake of teams, games, markets, and American-odds quotes for spread, total, and moneyline wagers.
- **Strict module separation** — Ledger accounting is isolated from college-football domain logic so the core can adapt to other paper-investing use cases.
- **Automated settlement** — Record final scores and let the ledger credit balances with a verifiable transaction trail.
- **Quality gates** — Ruff formatting/linting, pytest with coverage, and pre-commit hooks enforced on every change.

> **Responsible use:** Edgebook is exclusively a paper-trading and education sandbox. It will never process real money or interface with real-money wagering markets. See [`docs/security.md`](docs/security.md).

---

## Tech Stack

| Category | Technology | Notes |
|----------|------------|-------|
| Language | Python 3.11 | Pinned via `.python-version` |
| Environment | [uv](https://github.com/astral-sh/uv) | Dependency resolution and runner |
| Web framework | FastAPI | REST API engine |
| ORM | SQLAlchemy 2.0+ | Database abstraction |
| Database | PostgreSQL 15+ | System of record (SQLite for local dev) |
| Migrations | Alembic | Schema versioning |
| Lint/format | Ruff | Code quality |
| Testing | Pytest | Unit and integration tests |

---

## Getting Started

### Prerequisites

- **Python 3.11** ([Download](https://www.python.org/downloads/))
- **uv** ([Install](https://github.com/astral-sh/uv))
- **Git**

### Quick Start

1. **Clone and install:**
   ```bash
   git clone <repo-url>
   cd edgebook
   uv sync
   ```

2. **Run migrations and seed the database:**
   ```bash
   uv run alembic upgrade head
   ```

3. **Launch the API:**
   ```bash
   uv run uvicorn edgebook.main:app --reload
   # API docs at http://127.0.0.1:8000/docs
   ```

4. **Verify the setup:**
   ```bash
   uv run pytest
   uv run ruff check .
   ```

---

## Project Structure

```
edgebook/
├── src/edgebook/             # Application source
│   ├── main.py               # FastAPI app entry point
│   ├── core/                 # Config and database session
│   ├── api/                  # REST routes (accounts, cfb)
│   ├── cfb/                  # College football models & services
│   ├── ledger/               # Double-entry ledger models & services
│   └── utils/                # Shared utilities (logging)
│
├── alembic/                  # Database migrations
├── tests/                    # Test suite (api, ledger, core, utils)
├── docs/                     # Project and technical documentation
├── .agent/                   # AI agent guidance and skills
├── .codex/                   # Read-only context cache
├── session_logs/             # Development session history
├── config/                   # Configuration templates
├── pyproject.toml            # Dependencies and tooling
└── mkdocs.yml                # Documentation site config
```

---

## Essential Commands

```bash
# Format and lint
uv run ruff format . && uv run ruff check .

# Run tests with coverage
uv run pytest

# Run database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

# Serve documentation locally
uv run mkdocs serve  # http://127.0.0.1:8000
```

---

## Git Workflow

```bash
# CRITICAL: Never work on main
git branch
git checkout -b feat/<feature-name>

# Conventional commit format
git commit -m "feat: add simulated bet placement"
git commit -m "fix: correct ledger settlement for pushes"
git commit -m "docs: update API reference"
```

Branch types: `feat/`, `fix/`, `chore/`, `refactor/`, `docs/`.

---

## Key Documentation

| Document | Purpose |
|----------|---------|
| [`docs/project_charter.md`](docs/project_charter.md) | Vision, scope, users, and decision log |
| [`docs/project_brief.md`](docs/project_brief.md) | Objectives, success metrics, timeline |
| [`docs/implementation_schedule.md`](docs/implementation_schedule.md) | Phase roadmap and current priorities |
| [`docs/runbook.md`](docs/runbook.md) | Operational procedures |
| [`docs/security.md`](docs/security.md) | Responsible-use and simulation-only policy |
| [`docs/api/README.md`](docs/api/README.md) | API endpoint reference |
| [`.agent/CONTEXT.md`](.agent/CONTEXT.md) | Current project snapshot for AI sessions |

---

## Roadmap

Edgebook is developed in phases. See [`docs/implementation_schedule.md`](docs/implementation_schedule.md) for full detail.

- **Phase 0 — Foundation** ✅ Complete
- **Phase 1 — Manual End-to-End Betting Flow** ▶ In Progress
- **Phase 2 — Product Hardening** — ledger controls, parlays/teasers
- **Phase 3 — Analytics** — ROI, unit stats, and stake-allocation calibration
- **Phase 4 — External Ingestion** — CFB API integration
- **Phase 5 — AI-Assisted Review** — rationale and bias detection
- **Phase 6 — Investment Adaptability Review**

---

## Contributing

Contributions are welcome. Please:

1. Create a feature branch (never work on `main`).
2. Follow the standards in [`docs/development_standards.md`](docs/development_standards.md).
3. Run the health check before committing (see [`.agent/workflows/health-check.md`](.agent/workflows/health-check.md)).
4. Add or update tests; keep coverage above the target.
5. Open a pull request with a clear description.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full guide.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
