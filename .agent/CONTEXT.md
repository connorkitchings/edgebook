# Context Router (ACE Framework)

> **Welcome.** This repository utilizes the Agentic Context Engineering (ACE) framework. This document is your routing hub. Do not look for deep project details here—follow the pointers below.

## 🗺️ Map of the Repo

```text
Vibe-Coding/
├── .agent/              # 🧠 AI Agent Brain (You are here)
│   ├── CONTEXT.md       # Context Router (This file)
│   ├── PLAYBOOK.md      # Dynamic memory: Rules, Strategies, and Patterns
│   ├── skills/          # Executable workflows and procedures
│   └── workflows/       # Health checks and CI automation
├── src/                 # Application source code
├── tests/               # Pytest suite
├── docs/                # Architecture, guides, and manuals
├── scripts/             # Internal utilities and CLI tools
├── session_logs/        # Historical logs of AI sessions
└── config/              # Environment and system configs
```

## 🧭 Navigation Instructions

- **For Execution & Workflows:** Proceed to `.agent/skills/CATALOG.md` and load the appropriate skill for your task (e.g., `start-session` or `end-session`).
- **For Project State & Rules:** Read `.agent/PLAYBOOK.md` to understand current strategies, rules, and success patterns.
- **For Fast Commands:** Review `.codex/QUICKSTART.md`.
- **For Immediate Context:** Check the latest log in `session_logs/`.

---

## 🔄 Post-Session Protocol

**MANDATORY BEFORE EXIT:**
Before concluding any session, the AI agent MUST perform a self-critique and execute the following Reflection Protocol:

1. **Review Actions**: What code was changed? What new patterns emerged?
2. **Update PLAYBOOK**: If a new Success Pattern, Strategy, or Rule was identified during this session, you MUST append or modify `.agent/PLAYBOOK.md` to persist this learning.
3. **Log the Session**: Ensure a complete session log is written to `session_logs/` utilizing the `vibe_sync.py end` script or standard ending skills.
