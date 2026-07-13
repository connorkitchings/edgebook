# Lessons Learned

> Patterns and mistakes to avoid. Review at session start. Update after any correction.

---

## How to Use This File

1. **Review at session start** — Check for relevant lessons before starting work
2. **Add after corrections** — Whenever the user corrects you, capture the pattern
3. **Iterate ruthlessly** — Refine rules until the same mistake stops happening

---

## Correction Patterns

> Lessons from user corrections. Each entry captures the mistake, the rule to prevent it, and the date.

### [Date: 2026-07-11]

**Mistake:**
> Assumed the Alembic CLI would inherit `DATABASE_URL` from application settings during Docker deployment.

**Root Cause:**
> The migration environment used the static `alembic.ini` URL directly, so the migration container silently applied revisions to its local SQLite database instead of Postgres.

**Rule Added:**
> For every deployment target, smoke-test a fresh database and assert both the Alembic head revision and application health; ensure Alembic resolves the same database URL as the application while preserving explicit test overrides.

**Example:**
> The Compose smoke script starts an empty Postgres volume, reads `alembic_version`, compares it to `alembic heads`, then verifies `/health` before cleanup.

### [Date: 2026-07-11]

**Mistake:**
> Treated the schedule's explicit confidence field as a settled requirement for simulated bets.

**Root Cause:**
> Followed stale roadmap wording without checking whether the proposed field duplicated a stronger domain signal.

**Rule Added:**
> Before implementing subjective scoring metadata, check whether an objective behavioral measure already captures the same concept; for Edgebook, derive conviction from stake divided by pre-bet bankroll.

**Example:**
> Snapshot `bankroll_before_cents` and analyze stake allocation instead of asking for a separate confidence rating.

### [Date: 2026-07-12]

**Mistake:**
> Accepted Alembic autogeneration's index-renaming output without first reconciling model metadata with the repository's existing explicit index names.

**Root Cause:**
> Several older migrations used custom index names while their ORM columns used `index=True`, which made Alembic interpret equivalent indexes as schema changes.

**Rule Added:**
> Review autogen output before applying it; when prior migrations use named indexes, express those same names explicitly in ORM metadata and keep new migrations limited to intended schema changes.

**Example:**
> Preserve `ix_provider_observation_game` and add only the new run index instead of dropping and recreating unrelated indexes.

### [Date: 2026-07-12]

**Mistake:**
> Used `HTMLResponse | RedirectResponse` return union type annotations on FastAPI routes.

**Root Cause:**
> FastAPI tries to parse the return type annotation to compile a Pydantic response model, throwing a `FastAPIError` when encountering non-Pydantic class types in a Union.

**Rule Added:**
> For FastAPI endpoint routes returning non-Pydantic response classes (such as HTML or Redirect responses) in a union, annotate the return type as `Any` to prevent FastAPI from attempting response model parsing.

**Example:**
> Annotate page handlers that return templates or redirects with `-> Any`.

### [Date: 2026-07-12]

**Mistake:**
> Attempted to set `account_id = None` to test empty dashboard/bets states for users.

**Root Cause:**
> The database enforces a `NOT NULL` constraint on `auth_users.account_id` to guarantee ledger atomic integration, causing the db session commit to fail on integrity.

**Rule Added:**
> When simulating empty relationship states for models with database-enforced non-null constraints, toggle logical flags (such as `account.is_active = False`) in test setup and ensure view queries filter by those flags, rather than setting foreign keys to `None`.

**Example:**
> Verify `account.is_active` in page views, and set `account.is_active = False` in "no account" test fixtures.

### [Date: 2026-07-12]

**Mistake:**
> Phase 8.1 added a production SECRET_KEY validator, but session-end verification ran `mypy` only on the edited file and skipped the Docker smoke check, shipping a change that turned CI red (the validator crashed the smoke-test app, which runs under ENV=production with no SECRET_KEY).

**Root Cause:**
> Verification was scoped to the touched file instead of the project-wide gates CI actually runs (`mypy src/`, the docker smoke), and the downstream consumer (`docker-compose.yml`) was not audited when introducing a fail-fast guard.

**Rule Added:**
> Before declaring a session done, run the project's full verification suite (`uv run mypy src/`, `uv run ruff check .`, `uv run pytest`, and `scripts/docker_smoke.sh` when Docker is available) — not just the edited file. When introducing a fail-fast validator, enumerate every place the validated object is constructed under the affected condition and update them in the same change.

**Example:**
> After adding the production SECRET_KEY guard, also supply a valid SECRET_KEY in `docker-compose.yml` (smoke) and confirm both `mypy src/` and the smoke stack pass.

### [Date: 2026-07-13]

**Mistake:**
> Claimed "no CHANGELOG.md exists currently" in the Phase 8.5 plan and overwrote the file with `Write`; a CHANGELOG.md already existed in HEAD (initial foundation entry dated 2026-07-10).

**Root Cause:**
> Relied on memory of an earlier skim instead of verifying with `git ls-files`/`glob`. The `Write` tool's read-before-write guard did not catch it because the file had not been read in the session.

**Rule Added:**
> Before asserting a file does or does not exist (especially before creating or overwriting it), verify with `git ls-files '<path>'` or `glob`. When planning a new artifact, check the index, not just the working tree. Prefer `edit` over `write` for any file that might already be tracked.

**Example:**
> `git ls-files 'CHANGELOG.md'` returned the path, showing it was tracked; the new content should have been merged into `[Unreleased]` with the original `[0.1.0]` entry preserved verbatim.

---

### Template for New Entries

```markdown
### [Date: YYYY-MM-DD]

**Mistake:**
> [Brief description of what went wrong]

**Root Cause:**
> [Why it happened - be honest]

**Rule Added:**
> [Specific actionable rule]

**Example:**
> [What you should have done]
```

---

## Categories

### Code Quality
- [ ] Lazy fixes / temporary workarounds
- [ ] Missing tests
- [ ] Over-engineering
- [ ] Not considering edge cases

### Process
- [ ] Not planning before implementing
- [ ] Skipping verification
- [ ] Not asking clarifying questions
- [ ] Implementing without approval

### Context
- [ ] Not reading relevant docs first
- [ ] Missing important files
- [ ] Not checking recent session logs
- [ ] Ignoring existing patterns in codebase

### Communication
- [ ] Not explaining changes
- [ ] Making assumptions without checking
- [ ] Not providing options
- [ ] Missing handoff notes

---

## Review Checklist

Before each session, check:

- [ ] Read last 10 entries for relevant patterns
- [ ] Any new lessons since last session?
- [ ] Rules still make sense / haven't become outdated?

---

## Success Metrics

Track improvement over time:

- [ ] Fewer repeated mistakes
- [ ] Corrections decrease over time
- [ ] Rules are specific and actionable

---

## Links

- Principles: `.agent/PRINCIPLES.md`
- Session lifecycle: `.agent/skills/session-lifecycle/SKILL.md`

---

**Update this file after EVERY correction. The goal is to make the same mistake once.**
