# Edgebook Code Quality & Development Guide

This guide establishes the coding standards, code formatting rules, testing requirements, and instructions for working with AI assistants on the Edgebook platform.

---

## 🛠️ Code Standards

### Python Style
* **Formatting:** All code is strictly formatted using `ruff` with a line-length limit of 88.
* **Linter Rules:** Ruff is configured to enforce standard rules (E, F, I, N, W). Run `uv run ruff check .` before checking in code.
* **Type Annotations:** Explicit type hints are mandatory for all public functions, classes, and variables.
* **Future Imports:** Use `from __future__ import annotations` in Python modules to support modern type hints.

### Database Conventions
* **Alembic Migrations:** All schema changes must be accompanied by an Alembic migration script. Write migrations that can upgrade and downgrade successfully.
* **Model Imports in env.py:** Ensure new models are imported inside `alembic/env.py` so that autogenerate functions detect updates correctly.

---

## 🧪 Testing & Verification

Every feature, refactor, or bug fix must have test coverage.

* **Framework:** Pytest with `pytest-cov` is used to measure test metrics.
* **Coverage Gating:** The repository has a strict **minimum coverage gate of 80%**. The test coverage must not decrease when adding changes.
* **Verification Command:**
  ```bash
  uv run pytest
  ```
  This command will run all unit tests, print a term-missing coverage report, and write HTML coverage reports to `htmlcov/`.

---

## 🔒 Pre-Commit & Quality Checks

The workspace relies on git hooks to ensure no bad code is committed.

* **Hooks Configuration:** Configured via `pre-commit` (installed as a dev dependency).
* **Setup Hooks:**
  ```bash
  uv run pre-commit install
  ```
* **Run Manual Check:**
  ```bash
  uv run pre-commit run --all-files
  ```
  The hooks will automatically verify Ruff formatting, Ruff checks, and basic file hygiene before allowing any commit to proceed.

---

## 🤖 AI-Assisted Workflows

When working with an AI coding copilot inside the repository:
* **Plan First:** For non-trivial modifications, enter plan mode. Create an implementation plan detailing the files that will be added or modified, and get approval first.
* **Keep Changes Small:** Avoid large, all-encompassing commits. Break changes down into sequential, manageable tasks and track them inside a local task file.
* **Self-Improvement:** If the copilot makes an error or receives feedback, it must document the correction inside the local lessons catalog to prevent the mistake from reoccurring.
