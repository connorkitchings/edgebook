# Edgebook - Agent Context Router

This router file contains the active branch, repository status, and quick references.

---

## 🗺️ Project Snapshot

* **Product:** Edgebook (Simulated college football bankroll allocator)
* **Current Phase:** Phase 8 — Hosted MVP Operations code complete (8.1–8.5; live Oracle VM, provider credentials, and HTTPS remain externally deferred)
* **Architecture:** FastAPI modular monolith with explicit application orchestration
* **Active Branch:** `codex/verify-phase-8-sessions`

---

## 🧭 Authoritative Docs

* **Product Manual:** [product_manual.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/product_manual.md)
* **Development Guide:** [development_guide.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/development_guide.md)
* **Implementation Schedule:** [implementation_schedule.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/implementation_schedule.md)
* **Runbook:** [runbook.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/runbook.md)
* **Security Policies:** [security.md](file:///Users/connorkitchings/Desktop/Repositories/edgebook/docs/security.md)

---

## 🏃 Validation Commands

```bash
# Code Formatter & Linter
uv run ruff format .
uv run ruff check .

# Full Test Suite
uv run pytest
```
