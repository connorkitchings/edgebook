---
name: start-session
description: "Initialize a new development session. Load context, check branch safety, review recent work, produce planning output. DO NOT implement until user approves."
metadata:
  trigger-keywords: "start, kickoff, begin, session, new task, hello, hi"
  trigger-patterns: "^start session, ^kickoff, ^begin work"
---

# Start Session Skill

Use this skill to begin every development session safely and effectively.

## When to Use

- Starting any new development session
- Beginning a new task or feature
- After long breaks or context loss
- When switching to a different work stream

## Inputs

- User request (what they want to accomplish)
- Current branch status
- Recent session logs (last 3-5 from `session_logs/`)

## Steps

### 1. Branch Safety Check (CRITICAL)

**Never work on `main` branch.**

```bash
# Check current branch
git branch

# If on main, create feature branch immediately:
git checkout -b <branch-type>/<descriptive-name>

# Branch types:
# - feat/     New features
# - fix/      Bug fixes
# - chore/    Maintenance
# - refactor/ Code restructuring
# - docs/     Documentation
```

If uncommitted changes on main:
```bash
git stash
git checkout -b <branch-name>
git stash pop
```

### 2. Load Required Context (Tiered)

**Tier 1 - Minimal (ALWAYS read first):**
- `.agent/CONTEXT.md` — Project snapshot, current status, critical rules
- `.agent/skills/CATALOG.md` — Available skills for common tasks

**Tier 2 - As needed for specific task:**
- `README.md` — Project overview
- `AGENTS.md` — Agent roles and guidance
- `docs/implementation_schedule.md` — Current priorities

**Tier 3 - Deep dive (on-demand only):**
- `docs/architecture/` — Architecture decisions
- Specific code modules being modified

### 3. Understand Current Project State

**Read from `.agent/CONTEXT.md`:**
- Project status and current focus
- Active constraints and critical rules
- Technology stack and architecture

**Check Recent Work:**
- Read last 3-5 session logs from `session_logs/`
- Identify completed, in-progress, and blocked work
- Note any open decisions or TODOs

**Check Lessons Learned:**
- Read `.agent/tasks/lessons.md` for patterns to avoid
- Note any relevant lessons for the current task
- This is part of the Self-Improve principle

### 4. (Optional) Inject Previous Context

If continuing from a previous session (or switching tools), optionally inject context:

**With cli-continues:**
```bash
# List available sessions
continues list

# Resume a specific session
continues resume <session-id>

# Or cross-tool handoff
continues resume <session-id> --in <target-tool>
```

**Without cli-continues:**
- Read relevant session logs manually
- Review files mentioned in handoff notes
- Run status commands to verify current state

See `.agent/workflows/session-handoff.md` for detailed workflow.

### 5. Produce Planning-Only Output

**CRITICAL: No code, no diffs, no implementation yet.**

Your output must include:

#### A. Project Status Summary

- **Current State**: Brief status from CONTEXT.md
- **Active Branch**: Current working branch
- **Recent Work**: Summary of last 3-5 session logs
- **Blockers**: Any implementation blockers
- **Documentation Alignment**: Any contradictions found

#### B. Roadmap Options (3-6 alternatives)

For each option provide:
- **Goal**: What will be accomplished
- **Why**: How it helps the project
- **Prerequisites**: What must be done first
- **Risks**: What could go wrong
- **Deliverables**: Concrete outputs
- **Effort**: S/M/L

**Common Option Categories:**
1. Feature Implementation
2. Bug Fixes / Technical Debt
3. Testing & Validation
4. Documentation Updates
5. Infrastructure / DevOps
6. Code Refactoring

#### C. Questions for the User

Ask specific questions that must be answered before selecting a plan:
- Which feature or area to prioritize?
- Any constraints or deadlines?
- Target completeness or speed?
- Any specific concerns or risks?

### 5. Wait for User Approval

**Stop after producing the roadmap.**

- DO NOT modify any files during planning phase
- DO NOT generate code
- DO NOT execute a plan
- Wait for explicit user approval before taking action
- Confirm which roadmap option to pursue

## Validation

Before proceeding to implementation, confirm:
- [ ] You are NOT on `main` branch
- [ ] Context loaded from `.agent/CONTEXT.md`
- [ ] Recent session logs reviewed
- [ ] (Optional) Previous context injected via cli-continues
- [ ] Planning output produced with roadmap options
- [ ] User has selected and approved a plan

## Common Mistakes to Avoid

1. **Working on main** — Always check branch first
2. **Implementing without approval** — Wait for explicit user selection
3. **Loading too much context** — Use tiered approach, fetch on-demand
4. **Missing recent logs** — Always check last 3-5 session logs
5. **Skipping questions** — Ask clarifying questions before planning

## Rollback

If you discover you're on the wrong branch:
```bash
git stash  # Save work
git checkout main
git checkout -b correct/branch-name
git stash pop  # Restore work
```

## Handoff Packet Template

When starting work, use this template to capture initial context:

```text
Task: [Brief task description]
DoD: [Definition of done]
Files: [Key files to examine]
Constraints: [Timebox, scope, context budget]
Artifacts: [Expected outputs]
Rollback: [If applicable]
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
- End session: `.agent/skills/end-session/SKILL.md`
- Session logs: `session_logs/`
- Session handoff: `.agent/workflows/session-handoff.md`
- cli-continues docs: `docs/tools/cli-continues.md`

---

**Keep it systematic. Load minimal context. Plan before implementing.**
