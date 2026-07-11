# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Purged leftover template scaffolding so the repository is dedicated to Edgebook.

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
