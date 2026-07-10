# Quality Gates & Checklists

This document contains all quality gates and checklists to ensure high-quality, consistent,
and secure work throughout the development process.

## Definition of Done (DoD) {#definition-of-done}

This is the global standard for any task to be marked as "Done" in the `implementation_schedule.md`.

A task is considered Done only when:

- All code has been merged into the `main` branch
- All checks in the [Pre-Merge Checklist](#pre-merge) are complete
- The feature has been deployed to a staging or production environment
- The corresponding task in `implementation_schedule.md` is marked as ✅ Done

## Pre-Commit Checklist {#pre-commit}

Run this checklist before every git commit.

- [ ] **Code is formatted:** Ran `uv run ruff format .`
- [ ] **Linter passes:** Ran `uv run ruff check .` with zero errors
- [ ] **Code is self-documented:** Variables and functions have clear, intention-revealing names
- [ ] **No commented-out code:** Dead code has been removed
- [ ] **No hardcoded secrets:** API keys, passwords, etc., are loaded from environment variables
- [ ] **Commit message is descriptive:** Follows the convention in project_context.md

## Pre-Merge Checklist (Pull Request) {#pre-merge}

Run this more thorough checklist before merging a feature branch into main.

- [ ] **All Pre-Commit checks pass**
- [ ] **Feature works as intended:** Manually tested the primary user flow
- [ ] **Unit tests are written and passing:** All new logic is covered by tests
- [ ] **Test coverage has not decreased:** Run coverage report
- [ ] **Relevant documentation updated:** (`project_charter.md`, etc.) is updated
- [ ] **Data quality checks implemented:** New data sources and transformations are validated
- [ ] **Model performance validated:** Metrics meet criteria in the PRD/experiment plan
- [ ] **Security scan passed:** `uv run bandit -r src/` finds no high-severity issues
- [ ] **Security Review Checklist reviewed:** See [Security Review](#security-review) below
- [ ] **No "TODO" comments remain:** All temporary todos have been resolved or converted to tasks in
  implementation_schedule.md

## Security Review Checklist {#security-review}

A mandatory review for any feature handling user input, authentication, or data.

### Input & Data Validation

- [ ] **All user-provided data is sanitized and validated** on the server-side
- [ ] **SQL injection is prevented** (using parameterized queries/ORMs)
- [ ] **Cross-Site Scripting (XSS) is prevented** (output is properly encoded/escaped)

### Authentication & Authorization

- [ ] **Passwords are not stored in plain text** (hashed and salted)
- [ ] **Endpoints correctly verify authentication** that the user is authenticated
- [ ] **Endpoints correctly verify authorization** that the user is authorized to access/modify the
  specific resource

### Error Handling & Logging

- [ ] **Error messages are generic** and do not leak internal system details (e.g., stack traces)
- [ ] **Sensitive information is not logged** (passwords, API keys) is not present in logs
- [ ] **Security events are logged** for monitoring and incident response

### Data Protection

- [ ] **Sensitive data is encrypted** both in transit and at rest
- [ ] **Access controls are properly implemented** with principle of least privilege
- [ ] **Data retention policies are followed** with appropriate data cleanup

---

*This document consolidates all quality gates and checklists from the original checklist files
into a single, easily navigable reference with anchor links.*
