# Getting Started

> **Purpose:** Set up a local Edgebook development environment and run the simulation betting API.

---

## Prerequisites

- **Python 3.11** (pinned in `.python-version`)
- **[uv](https://github.com/astral-sh/uv)** — the project's package manager
- **Git**

## 1. Clone the Repository

```bash
git clone <repository-url>
cd edgebook
```

## 2. Install Dependencies

Edgebook uses `uv` for environment and dependency management:

```bash
uv sync
```

This creates a `.venv` virtual environment and installs all dependencies from `pyproject.toml` / `uv.lock`.

## 3. Run Database Migrations

Apply the schema (ledger + CFB models) to the local database:

```bash
uv run alembic upgrade head
```

## 4. Set Up Pre-Commit Hooks

Install the hooks so contributions adhere to the project's quality gates:

```bash
uv run pre-commit install
```

## 5. Verify the Setup

```bash
# Run the test suite with coverage
uv run pytest

# Lint and format
uv run ruff format . && uv run ruff check .
```

## 6. Run the API

```bash
uv run uvicorn edgebook.main:app --reload
```

Interactive API docs are available at `http://127.0.0.1:8000/docs`.

## 7. View the Documentation

To serve the MkDocs documentation site locally:

```bash
uv run mkdocs serve
```

Then open `http://127.0.0.1:8000` in your browser.

---

## Starting a Development Session

Edgebook follows an AI-assisted session workflow. To begin work:

1. Confirm you are **not** on `main` — create a feature branch:
   ```bash
   git checkout -b feat/<your-feature>
   ```
2. Read the project snapshot: [`.agent/CONTEXT.md`](../.agent/CONTEXT.md)
3. Follow the start workflow: [`.agent/skills/start-session/SKILL.md`](../.agent/skills/start-session/SKILL.md)
4. Review recent session logs in `session_logs/` for context.

You are now ready to start developing.
