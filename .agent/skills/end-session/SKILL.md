---
name: end-session
description: "Close a development session properly. Create session log, run health checks, update schedule, prepare handoff documentation."
metadata:
  trigger-keywords: "end, close, finish, wrap up, done, complete"
  trigger-patterns: "^end session, ^wrap up, ^finish work"
---

# End Session Skill

Use this skill to close every development session properly and prepare handoff for the next session.

## When to Use

- Completing any development session
- Before taking a break from the project
- After finishing a feature or task
- When context needs to be preserved for next session

## Inputs

- Work completed during session
- Files modified
- Tests run and results
- Any blockers or issues encountered

## Steps

### 1. Create Session Log

Create a new log file in `session_logs/MM-DD-YYYY/N - Title.md` where:
- Folder: `MM-DD-YYYY` (e.g., `02-11-2026`)
- File: `N - Title.md` (e.g., `1 - Feature Implementation.md`)
- N = Sequential number for that day (1, 2, 3...)
- Title = Concise description of session

**Session log template:**

```markdown
# Session Log — YYYY-MM-DD (Session NN)

## TL;DR (≤5 lines)
- **Goal**: [What was the intended outcome]
- **Accomplished**: [What was completed]
- **Blockers**: [Any issues or blockers]
- **Next**: [What should happen next]
- **Branch**: [Feature branch name]

**Tags**: ["feature", "bugfix", "docs", "testing", etc.]

---

## Context
- **Started**: HH:MM
- **Ended**: HH:MM
- **Duration**: ~X hours
- **User Request**: [Original user request]

## Work Completed

### Files Modified
- `path/to/file1.py` - [What changed]
- `path/to/file2.py` - [What changed]

### Tests Added/Modified
- `tests/test_feature.py` - [New test cases]

### Commands Run
```bash
# Commands executed during session
uv run pytest
uv run ruff format .
```

## Decisions Made
- [Key decision 1 and rationale]
- [Key decision 2 and rationale]

## Issues Encountered
- [Issue 1 and resolution/workaround]
- [Issue 2 and status]

## Next Steps
1. [Next action item]
2. [Next action item]
3. [Next action item]

## Handoff Notes
- **For next session**: [Context needed]
- **Open questions**: [Unresolved questions]
- **Dependencies**: [Waiting on what?]

---

**Session Owner**: [AI tool used: Claude Code/Gemini/etc.]
**User**: [User name if applicable]
```

### 2. Capture Lessons Learned

**If the user corrected you during this session**, capture the lesson:

1. Open `.agent/tasks/lessons.md`
2. Add a new entry with:
   - Date
   - What went wrong (mistake)
   - Root cause
   - Rule to prevent recurrence

This is part of the **Self-Improve** principle. The goal is to make each mistake only once.

**If no corrections occurred**, skip this step.

See `.agent/tasks/lessons.md` for the template.

### 3. (Optional) Prepare Session for Handoff

If you may continue in a different AI tool, optionally prepare for handoff:

**With cli-continues:**
```bash
# List sessions to verify discovery
continues list
# Note: Session will be automatically discoverable
```

**Without cli-continues:**
Document context manually in session log:
- Current work state
- Files being modified
- Recent decisions
- Open questions

See `.agent/workflows/session-handoff.md` for detailed workflow.

### 4. Run Health Checks

Execute the health check workflow:

```bash
# Health check workflow
Follow steps in .agent/workflows/health-check.md
```

**If health check fails:**
- Document the failure in session log
- Fix issues or note them for next session
- DO NOT commit broken code

### 5. Update Implementation Schedule

If tasks were completed:
- Open `docs/implementation_schedule.md`
- Update task status (mark completed tasks)
- Add new tasks if discovered
- Note any timeline impacts

### 6. Prepare Commit

**DO NOT commit directly.** Propose a commit message for user review:

```bash
# Proposed commit message format:
<type>: <short description>

<detailed description>
- What changed
- Why it changed
- Any breaking changes

Refs: session_logs/YYYY-MM-DD/NN.md
```

**Commit types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks
- `perf:` Performance improvements

### 7. Document Handoff

Create handoff documentation for the next session:

**What to document:**
- Current state of work (completed, in-progress, blocked)
- Files to review first
- Known issues or technical debt
- Questions that need answering
- Recommended next steps

**Where to document:**
- Session log (Handoff Notes section)
- Implementation schedule (task notes)
- Code comments (for complex logic)

## Validation

Before ending session, confirm:
- [ ] Session log created in `session_logs/`
- [ ] Lessons captured (if user corrected you during session)
- [ ] (Optional) Session prepared for handoff with cli-continues
- [ ] Health check passed (or failures documented)
- [ ] Implementation schedule updated if tasks completed
- [ ] Commit message proposed (not executed)
- [ ] Handoff notes documented
- [ ] All work saved and pushed to feature branch (if ready)

## Common Mistakes to Avoid

1. **Skipping session log** — Every session needs a log
2. **Not running health check** — Always validate before closing
3. **Committing without user approval** — Propose, don't execute
4. **Missing handoff notes** — Next session needs context
5. **Forgetting to update schedule** — Keep schedule current

## Health Check Failures

If health check fails:

**Linting failures:**
```bash
uv run ruff check . --fix  # Auto-fix where possible
uv run ruff format .        # Format code
```

**Test failures:**
```bash
uv run pytest -vv           # Verbose output
uv run pytest --lf          # Re-run last failed
```

**Document in session log:**
- Which checks failed
- Why they failed
- What needs to be fixed
- Whether it's blocked or ready for next session

## Session Log Location

Organize logs by date with descriptive titles:
```
session_logs/
├── 02-11-2026/
│   ├── 1 - Feature Implementation.md
│   ├── 2 - Bug Fix.md
│   └── 3 - Documentation Update.md
├── 02-12-2026/
│   └── 1 - Testing Session.md
└── TEMPLATE.md  # Template for new logs
```

## Handoff Notes Template

Document these for the next session:

```markdown
## Handoff Notes
- **Current state**: [What was accomplished/in-progress/blocked]
- **Last file edited**: [File path and line number]
- **Blockers**: [Any issues preventing progress]
- **Next priority**: [What should happen next]
- **Open questions**: [Unresolved questions]
- **Context needed**: [What next agent needs to know]
```

---

## Links

- Context: `.agent/CONTEXT.md`
- Principles: `.agent/PRINCIPLES.md`
- Skills catalog: `.agent/skills/CATALOG.md`
- Agent guidance: `.agent/AGENTS.md`
- Implementation schedule: `docs/implementation_schedule.md`
- Lessons learned: `.agent/tasks/lessons.md`
- Workflow orchestration: `.agent/workflows/workflow-orchestration.md`
- Start session: `.agent/skills/start-session/SKILL.md`
- Health check: `.agent/workflows/health-check.md`
- Session handoff: `.agent/workflows/session-handoff.md`
- cli-continues docs: `docs/tools/cli-continues.md`

---

**Close properly. Document thoroughly. Prepare for handoff.**
