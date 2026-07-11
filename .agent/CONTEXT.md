# Edgebook - Agent Context Router

> **Welcome.** This repository contains **Edgebook**, a college football paper-betting simulation platform. This router file lists the current status and directory navigation references.

---

## 🗺️ Project Snapshot

- **Product:** Edgebook (Simulated college football bankroll allocator)
- **Current Phase:** Phase 4 planning (Phase 3 analytics complete)
- **Architecture:** FastAPI backend, SQLAlchemy database layers, modular monolithic boundary separation.
- **Active Branch:** `feat/manual-betting-flow`

---

## 🧭 Navigation & Authoritative Docs

- **Project Charter:** [project_charter.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/project_charter.md)
- **Project Brief:** [project_brief.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/project_brief.md)
- **Implementation Schedule:** [implementation_schedule.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/implementation_schedule.md)
- **Runbook:** [runbook.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/runbook.md)
- **Security & Responsible Use:** [security.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/security.md)

---

## 🏃 Validation Commands

Verify repository state before and after commits:

```bash
# Run code formatter
uv run ruff format .

# Run code linter
uv run ruff check .

# Run complete test suite (with coverage)
uv run pytest

# Launch local API development server
uv run uvicorn edgebook.main:app --reload
```

---

## 🎯 Next Prioritized Task

- Plan **Phase 4 External Ingestion**: CFB API integration to ingest games, schedules, and scores automatically.
