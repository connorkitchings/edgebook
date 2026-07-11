---
name: session-lifecycle
description: "Initialize and finalize development sessions safely. Includes branch checks, planning summaries, quality verification, and logging."
metadata:
  trigger-keywords: "start, kickoff, begin, end, close, finish, wrap up, session"
  trigger-patterns: "^start session, ^end session"
---

# Session Lifecycle Skill

Use this skill to start and end development sessions cleanly.

---

## 🚀 Starting a Session

### 1. Branch Safety Check
Never work on `main`. Create or switch to a feature branch:
```bash
git branch
# Create branch: git checkout -b feat/your-feature
```

### 2. Produce Planning Output
Before writing code, summarize:
* **Current State:** Active branch and status.
* **Roadmap Options:** 3-6 alternatives detailing goals, risks, deliverables, and effort.
* **Clarifications:** Questions for the user to select the path.

Wait for user approval before writing code.

---

## 🏁 Ending a Session

### 1. Verification
Ensure all code conforms to project standards:
```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

### 2. Create Session Log
Write a log file under `session_logs/YYYY-MM-DD/` named `X - Description.md` where X is the sequence number:
```markdown
# Session Log — YYYY-MM-DD (Session XX)

## TL;DR
* **Goal:** [Brief goal description]
* **Accomplished:** [Bullet list of work done]
* **Branch:** [Active branch name]

## Work Completed
* Detail changes to files.

## Verification
* Test and Ruff check outcomes.

## Decisions Made
* Context or rationale for key decisions.
```
