# AGENTS.md — AI Agent Operating Manual

This manual defines the mandates and roles for AI-assisted development inside the Edgebook repository.

---

## 👥 AI Roles

### 1. Navigator (Architect / Triager)
* **Mandate:** High-level coordinator, planner, and evaluator.
* **Responsibilities:**
  * Triages incoming requests and produces 3-7 line plans.
  * Confirms goals, definitions of done, and architectural constraints.
  * Formulates verification criteria and evaluates overall outcomes.
  * Maintains project status, roadmap charts, and schedules.

### 2. Developer (Executor / Tester)
* **Mandate:** Implementation, refactoring, and quality assurance.
* **Responsibilities:**
  * Implements code changes conforming strictly to module boundaries.
  * Formulates type hints and enforces ruff format/lint standards.
  * Writes unit and integration tests for all modified logic.
  * Resolves failing tests, lints, or static checks.

---

## 🏃 Operating Rules

1. **Every PR Must Include Tests:** Unit tests are required for any logic change. Code coverage must meet the 80% minimum threshold.
2. **Format and Lint:** Format code using `uv run ruff format .` and verify lints using `uv run ruff check .` before staging changes.
3. **Plan First:** For non-trivial modifications (3+ steps or architectural changes), formulate an implementation plan and get user feedback before starting.
4. **Append-Only Invariant:** Preserve the append-only ledger transaction structure. Always verify transactions balance to zero.
5. **Lessons Learned:** After any correction, write the root cause and a preventive rule to `.agent/tasks/lessons.md`.
