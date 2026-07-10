# Session Handoff Workflow

Transfer AI coding session context between tools using cli-continues.

---

## When to Use

- Switching from one AI coding tool to another
- Resuming work after hitting rate limits
- Continuing a session on a different machine
- Sharing context between team members using different tools

---

## Prerequisites

1. **cli-continues installed** (optional but recommended):
   ```bash
   npx continues
   # or
   npm install -g continues
   ```

2. **Node.js 22+** (for cli-continues):
   ```bash
   node --version
   ```

---

## Option A: Using cli-continues (Recommended)

### Step 1: Prepare Session for Handoff (End Session)

```bash
# List all sessions to verify discovery
continues list

# Note the session ID for your current session
```

### Step 2: Resume in Target Tool (Start Session)

```bash
# Interactive mode - browse and select
continues

# Or directly resume a specific session
continues resume <session-id> --in <target-tool>

# Example: Resume Claude session in Gemini
continues resume abc123 --in gemini
```

### Cross-Tool Matrix

| From → To | Claude | Copilot | Gemini | Codex | OpenCode | Droid | Cursor |
|-----------|--------|---------|--------|-------|----------|-------|--------|
| Claude    | —      | ✅      | ✅     | ✅    | ✅       | ✅    | ✅     |
| Copilot   | ✅     | —       | ✅     | ✅    | ✅       | ✅    | ✅     |
| Gemini    | ✅     | ✅      | —      | ✅    | ✅       | ✅    | ✅     |
| Codex     | ✅     | ✅      | ✅     | —     | ✅       | ✅    | ✅     |
| OpenCode  | ✅     | ✅      | ✅     | ✅    | —        | ✅    | ✅     |
| Droid     | ✅     | ✅      | ✅     | ✅    | ✅       | —     | ✅     |
| Cursor    | ✅     | ✅      | ✅     | ✅    | ✅       | ✅    | —      |

---

## Option B: Manual Handoff (Without cli-continues)

If cli-continues is not available, use manual handoff:

### Step 1: Document Current Session (End Session)

Create a handoff document with:

```markdown
## Session Handoff

### Current Work
- [What you were working on]
- [Files being modified]

### Context
- [Recent decisions made]
- [Open questions]
- [Blockers or issues]

### Tool Activity
- [Commands run recently]
- [Files edited]
- [Tests run]

### Next Steps
1. [Immediate next action]
2. [Follow-up task]
```

### Step 2: Transfer to New Tool (Start Session)

When starting in the new tool:
1. Read the handoff document
2. Load relevant files
3. Run recent commands to verify state
4. Continue work

---

## Detection: Is cli-continues Available?

Check if cli-continues is installed:

```bash
# Check if command exists
command -v continues || echo "not installed"

# Or try running it
npx continues --version 2>/dev/null || echo "not available"
```

---

## Graceful Degradation

If cli-continues is not available:

1. **End Session**: Document context manually in session log
2. **Start Session**: Read previous session logs for context
3. **Continue**: Proceed without automated handoff

The template works fully without cli-continues — it's an optional enhancement.

---

## Session Index

- **Location**: `~/.continues/sessions.jsonl`
- **TTL**: 5 minutes (auto-refresh)
- **Force rebuild**: `continues rebuild`

---

## Troubleshooting

### Sessions Not Appearing

```bash
# Force rebuild index
continues rebuild

# Check scan stats
continues scan
```

### Node Version Error

```bash
# Install Node 22+
nvm install 22
nvm use 22
```

### Rate Limit Hit

1. Note current session ID from `continues list`
2. Wait for limit reset, OR
3. Switch to different tool using handoff

---

## Integration with Skills

### End Session Skill

When using `.agent/skills/end-session/SKILL.md`:

1. Run `continues` before closing (optional)
2. Note session ID in handoff notes
3. Document key context for manual handoff

### Start Session Skill

When using `.agent/skills/start-session/SKILL.md`:

1. Run `continues list` to find previous sessions (optional)
2. Use `continues resume <id>` to inject context
3. Or read previous session logs manually

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `continues` | Interactive TUI picker |
| `continues list` | List all sessions |
| `continues list --source <tool>` | Filter by tool |
| `continues resume <id>` | Resume session |
| `continues resume <id> --in <tool>` | Cross-tool handoff |
| `continues scan` | Show discovery stats |
| `continues rebuild` | Force-rebuild index |

---

## Next Steps

After handoff:
1. Verify context loaded correctly
2. Check recent file changes
3. Run status commands to confirm state
4. Continue development

---

**Links:**
- Tool docs: `docs/tools/cli-continues.md`
- End session: `.agent/skills/end-session/SKILL.md`
- Start session: `.agent/skills/start-session/SKILL.md`
- Skills catalog: `.agent/skills/CATALOG.md`
