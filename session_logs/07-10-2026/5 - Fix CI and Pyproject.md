# Session Log — 07-10-2026 (5 - Fix CI and Pyproject)

> **PR 3 of 3** in the phased template-purge effort. Makes CI, packaging, and tooling reflect Edgebook reality.

---

## TL;DR (≤5 lines)
- **Goal**: Fix CI workflows, pyproject.toml, Makefile, and pre-commit so tooling is correct for Edgebook.
- **Accomplished**: Removed template deps/extras, added missing `docs` extra + mypy, fixed CI Python versions + deleted validate-template job, fixed Makefile targets, dropped nbstripout, fixed 11 broken doc links so `mkdocs build --strict` is green.
- **Blockers**: None.
- **Next**: Phased purge complete; resume Task 1.3 (Place Simulated Bet).
- **Branch**: `chore/fix-ci-and-pyproject`

**Tags**: ["chore", "ci", "tooling", "template-purge"]

---

## Context
- **User Request**: Dedicate the entire repo to Edgebook.
- **AI Tool**: OpenCode (glm-5.2)
- **Approach**: PR 3 — CI + packaging + tooling correctness only.

## Work Completed

### pyproject.toml
- Removed unused template runtime deps: `typer`, `rich`, `pyperclip`, `requests` (verified zero imports in `src/edgebook/`).
- Removed `data-science` and `mlops` optional-dependency extras (no notebooks/ML in Edgebook).
- Removed duplicate `[project.optional-dependencies].dev` (consolidated to `[dependency-groups].dev`).
- Added new `docs` extra (`mkdocs`, `mkdocs-material`, `mkdocstrings`, `mkdocstrings-python`) — was missing despite mkdocs.yml using the mkdocstrings plugin.
- Added `mypy>=1.10` to dev group so the CI type-check job can run it.
- Bumped `--cov-fail-under` from 55 → 80 to match the project brief's ">80% coverage" standard.

### .github/workflows/ci.yml
- Bumped Python 3.10 → 3.11 across lint, type-check, security jobs.
- Test matrix reduced from `['3.10','3.11','3.12']` → `['3.11','3.12']` (requires-python is >=3.11).
- Deleted the entire `validate-template` job (ran deleted `scripts/validate_template.py`).

### .github/workflows/docs.yml
- Bumped Python 3.10 → 3.11 in both build and deploy jobs.
- `uv sync --extra docs` now resolves (new `docs` extra).

### Makefile
- Removed `setup` (ran deleted `scripts/setup_project.py`) and `validate` (ran deleted `scripts/validate_template.py`) targets.
- Added `migrate` target (`alembic upgrade head`).
- `docs`/`docs-serve` now sync the `docs` extra and build with `--strict`.

### .pre-commit-config.yaml
- Removed the `nbstripout` hook (no notebooks remain).

### Documentation links (made `mkdocs build --strict` green)
- Fixed wrong relative paths in `tools/pre_commit_hooks.md` (./ → ../) and `ai_guide.md` (`./docs/` → `./`).
- Converted cross-boundary links to plain backtick references in `index.md`, `getting_started.md`, `development_standards.md`, `project_charter.md`, `ai_guide.md` (README/CHANGELOG/.agent/.github are outside docs_dir).
- Replaced custom-anchor links in `checklists.md` with bold text references.

### Commands Run / Verified
```bash
uv sync                       # clean (removed typer/rich/pyperclip/requests; added mypy)
uv sync --extra docs          # clean (mkdocs + mkdocstrings installed)
uv run ruff format . --check  # 33 files already formatted
uv run ruff check .           # All checks passed
uv run pytest                 # 17 passed, 87.77% coverage (>=80 threshold)
uv run mkdocs build --strict  # ZERO warnings/errors
make all                      # format-check + lint + test green
curl /health                  # {"status":"ok",...database:"ok"}
```

## Decisions Made
- **Left pre-existing mypy error in `cfb/services.py:197`**: real Edgebook domain code, not template cruft; out of scope for the purge. CI type-check uses `|| true` so it's non-blocking.
- **Coverage threshold 55 → 80**: aligned with the project brief's stated ">80% test coverage" success metric. Current coverage is 88%, comfortably above.
- **Consolidated dev deps into `[dependency-groups].dev`**: removed the older `[project.optional-dependencies].dev` to avoid duplication; `uv sync` defaults include the dev group.

## Issues Encountered
- `mkdocs build --strict` initially aborted with 11 warnings + 2 anchor INFOs. Fixed all link issues; build is now clean. This validated that the PR 2 nav and the new `docs` extra work together end-to-end.
- `uv lock` regenerated (template deps dropped, mypy/docs added).

## Next Steps
1. Merge the three chore branches (PR 1 → 2 → 3) into `feat/project-initialization`, then to `main`.
2. Resume roadmap: **Task 1.3 — Place Simulated Bet** (connect open CFB market to `WAGER_STAKE` ledger postings).

## Handoff Notes
- **Phased purge COMPLETE.** The repo is now dedicated to Edgebook across source, docs, CI, and packaging.
- Optional future cleanup (not blocking): the `web-init` and `mcp-workflow` skills are unused by Edgebook (API-only so far) and could be deleted later.

---

**Session Owner**: OpenCode (glm-5.2)
**Related**: PR 1 (86d1b95, deletions), PR 2 (f9f0246, doc rebrand). Schedule next: Task 1.3.
