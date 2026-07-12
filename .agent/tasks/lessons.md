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

### [Date: YYYY-MM-DD]

**Mistake:**
> What went wrong (from user correction)

**Root Cause:**
> Why it happened

**Rule Added:**
> Specific rule to prevent this mistake

**Example:**
> What you should have done instead

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
