# Workflow Orchestration

> Task management patterns for AI-assisted development. Based on Matt Dancho's workflow principles.

---

## Task Management Loop

```
Plan → Verify → Execute → Verify → Document → Review
  ↑                                      |
  └──────────────────────────────────────┘
```

---

## Plan Phase

### Identify Task Scope

**Is this non-trivial?**
- 3+ steps involved?
- Architectural decisions?
- Multiple files affected?
- Tests needed?

**If YES → Enter Plan Mode**

### Write Plan

Document in session log or task file:

```
## Plan

### Task
[What needs to be done]

### Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Definition of Done
- [ ] [Requirement 1]
- [ ] [Requirement 2]

### Risks
- [Risk 1 and mitigation]

### Dependencies
- [What needs to happen first]
```

---

## Verify Before Starting

**Check in before implementing:**

- Does the plan make sense?
- Are there edge cases?
- Is there a simpler approach?
- What could go wrong?

**Ask the user:**
- "Does this plan work for you?"
- "Any concerns with this approach?"

---

## Execute Phase

### Track Progress

As you complete items:
- [ ] Mark steps complete in your working notes
- Update session log with progress
- Note blockers immediately

### Use Subagents

For complex problems, delegate:
- Research tasks → subagent
- Exploration → subagent  
- Parallel analysis → subagent
- One task per subagent

### Handle Issues

**If something goes wrong:**
1. STOP — don't keep pushing
2. Re-assess the plan
3. Fix the issue
4. Verify before continuing

---

## Verify Before Done

**Never mark complete without proving:**

1. **Run tests** — All pass locally
2. **Check behavior** — Diff before/after
3. **Ask yourself** — "Would a staff engineer approve this?"
4. **Demonstrate** — Show output, logs, results

---

## Document Results

### Session Log Update

Add to session log:

```markdown
## Results

### Completed
- [ ] Task 1
- [ ] Task 2

### Verification
- Tests: [pass/fail]
- Behavior: [matches intent]
- Review: [self-check complete]

### Issues Found
- [Any issues encountered]
```

### Capture Lessons

**If user corrected you:**
- Update `.agent/tasks/lessons.md`
- Write rule to prevent recurrence
- Review at next session start

---

## High-Level Summary

At each milestone, provide a summary:

```
## Progress

### Completed
- [What finished]

### In Progress
- [What's underway]

### Next
- [What's next]

### Blockers
- [Any blockers]
```

---

## Principles in This Workflow

| Principle | Application |
|-----------|-------------|
| Plan First | Always plan non-trivial tasks |
| Ship Small | Break into small, verifiable chunks |
| Verify Before Done | Prove it works, don't assume |
| Self-Improve | Capture lessons after corrections |
| Elegant When Non-Trivial | Pause and ask: "Is there a better way?" |

---

## Quick Reference

### Decision Tree: Is This Non-Trivial?

```
├─ 3+ steps? → YES → Plan Mode
├─ Architectural? → YES → Plan Mode
├─ Multiple files? → YES → Plan Mode
└─ Tests needed? → YES → Plan Mode
     ↓
   NO → Execute directly, but verify before done
```

### Verification Checklist

- [ ] Tests pass (`uv run pytest`)
- [ ] Lint clean (`uv run ruff check .`)
- [ ] Format clean (`uv run ruff format .`)
- [ ] Behavior verified (ran the code)
- [ ] Self-check: "Would a staff engineer approve?"

---

## Links

- Principles: `.agent/PRINCIPLES.md`
- Lessons: `.agent/tasks/lessons.md`
- Start session: `.agent/skills/start-session/SKILL.md`
- End session: `.agent/skills/end-session/SKILL.md`
- Health check: `.agent/workflows/health-check.md`
