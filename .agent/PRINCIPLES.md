# Operating Principles

> Core rules that guide every AI-assisted development session. These principles are non-negotiable.

---

## 1. Plan First

**For any non-trivial task (3+ steps or architectural decisions), enter plan mode.**

- Write detailed specs upfront to reduce ambiguity
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building

**What counts as non-trivial:**
- Any task with 3+ steps
- Architectural decisions
- New files or significant refactors
- Changes affecting multiple modules
- Anything requiring tests

---

## 2. Ship Small, Stay Simple

**Make every change as simple as possible. Impact minimal code.**

- Focused PRs are easier to review and safer to ship
- Avoid introducing unnecessary dependencies or complexity
- Every line of code is a liability — write only what's needed
- Question whether each file is truly necessary

---

## 3. Test-Driven

**Every feature needs tests. Every bug needs a regression test.**

- Write tests before code (TDD) when practical
- Run tests locally before committing
- Coverage should not decrease
- Failing tests = stop and fix

---

## 4. Minimal & Reversible

**Changes should only touch what's necessary. Prefer operations that can be rolled back.**

- Don't refactor code unless required by the task
- Feature flags over permanent changes when uncertain
- Document how to revert if needed
- Avoid breaking changes unless necessary

---

## 5. No Lazy Fixes

**Find root causes. No temporary fixes. Senior developer standards.**

- Don't patch symptoms — fix the underlying issue
- If you're about to add a comment explaining a hack, fix it properly instead
- Ask: "Would a staff engineer approve this?"
- Document why a fix was made a certain way

---

## 6. Elegant When Non-Trivial

**For non-trivial changes: pause and consider elegance. Skip for simple fixes — don't over-engineer.**

- If a fix feels hacky, step back and ask: "Knowing everything I know now, is there a more elegant solution?"
- Challenge your own work before presenting it
- Simple, obvious fixes don't need this — just implement them
- Non-trivial = 3+ changes or architectural impact

---

## 7. Verify Before Done

**Never mark a task complete without proving it works.**

- Run tests and verify they pass
- Check behavior matches intent
- Diff behavior between before/after when relevant
- Ask: "Would a staff engineer approve this?"
- Demonstrate correctness (run commands, show output)

---

## 8. Self-Improve

**After ANY correction from the user: capture the lesson.**

- Update `.agent/tasks/lessons.md` with the pattern that caused the mistake
- Write rules that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review relevant lessons at session start

---

## 9. Autonomous Bug Fixing

**When given a bug report: just fix it. Don't ask for hand-holding.**

- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how
- If you need clarification, ask — but propose a plan first

---

## 10. Subagent Strategy

**Use subagents to keep main context window clean.**

- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution
- Keeps main context fresh for coordination

---

## 11. Audited Actions

**Log important operations and decisions.**

- Document key decisions in session logs
- Capture why something was done, not just what
- Note assumptions and their sources
- Helps future sessions understand context

---

## Principles in Practice

### Daily Review
At session start, check for relevant lessons:
```
Read .agent/tasks/lessons.md for patterns to avoid
```

### After Corrections
Always capture the lesson:
```
Update .agent/tasks/lessons.md with what went wrong
```

### Before Completing
Verify, then verify again:
```
Run tests, check behavior, prove it works
```

---

## Links

- Context: `.agent/CONTEXT.md`
- Agent guidance: `.agent/AGENTS.md`
- Lessons capture: `.agent/tasks/lessons.md`
- Workflow orchestration: `.agent/workflows/workflow-orchestration.md`
- Skills catalog: `.agent/skills/CATALOG.md`

---

**These principles are not suggestions — they are how we operate.**
