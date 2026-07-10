# .codex/ — Read-Only Context Cache

> **Purpose**: Fast-access reference files for AI tools with context caching.

---

## What is .codex/?

The `.codex/` directory contains **read-only** reference documentation designed for:
- **Fast context loading**: Files optimized for AI context windows
- **Context caching**: Static content that rarely changes
- **Quick orientation**: Essential information in compact form

**Philosophy**: These files are "cached knowledge" — they provide quick answers without requiring deep file traversal.

---

## Files in This Directory

### MAP.md
**Purpose**: Visual project tree showing directory structure and key files
**Use when**: Need to understand project layout quickly
**Update frequency**: When major structural changes occur

### QUICKSTART.md
**Purpose**: Essential commands for common operations
**Use when**: Need to run tests, start servers, or perform routine tasks
**Update frequency**: When tooling or workflows change

### README.md (this file)
**Purpose**: Explain the .codex/ directory purpose
**Use when**: First time seeing .codex/ directory
**Update frequency**: Rarely (only when concept changes)

---

## Design Principles

1. **Read-Only**: These files are reference only, not working documents
2. **Compact**: Each file should be ≤ 200 lines
3. **Stable**: Content should change infrequently (good for caching)
4. **Self-Contained**: No external dependencies or links to volatile content
5. **Fast to Parse**: Clear structure, minimal prose

---

## When to Update

Update .codex/ files when:
- Major directory restructuring
- Core tooling changes (switching test runner, linter, etc.)
- Essential commands change
- File becomes stale or misleading

**Do NOT update for:**
- Individual feature additions
- Temporary experimental code
- In-progress work
- Session-specific context

---

## Relation to Other Docs

| Directory | Purpose | Update Frequency |
|-----------|---------|-----------------|
| `.agent/` | Active session management | Every session |
| `.codex/` | Static reference cache | Rarely (major changes only) |
| `docs/` | Detailed documentation | Regular (as features evolve) |
| `session_logs/` | Historical records | Every session |

---

## For AI Tools

If you're an AI assistant:
- **Load .codex/ files early**: They're optimized for context caching
- **Trust the content**: These files are maintained to be accurate
- **Don't modify**: These are reference files, not working documents
- **Supplement with .agent/**: Use .agent/ for current session state

---

**Think of .codex/ as the "quick reference card" for the project.**
