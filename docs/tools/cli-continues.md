# cli-continues — Session Handoff Tool

> Never lose context when switching between AI coding tools.

`cli-continues` is an optional utility that enables seamless session handoff between AI coding assistants. It reads session data from any supported tool and can inject that context into another tool.

---

## What It Does

- **Session Discovery** — Scans all supported tools for existing sessions
- **Cross-tool Handoff** — Transfer context between Claude, Copilot, Gemini, Codex, OpenCode, Factory Droid, and Cursor
- **Context Extraction** — Pulls conversation history, file changes, tool activity, and AI reasoning
- **Quick Resume** — One-command resume from any tool

---

## Supported Tools

| Tool | Session Location | Format |
|------|------------------|--------|
| Claude Code | `~/.claude/projects/` | JSONL |
| GitHub Copilot | `~/.copilot/session-state/` | YAML + JSONL |
| Gemini CLI | `~/.gemini/tmp/*/chats/` | JSON |
| OpenAI Codex | `~/.codex/sessions/` | JSONL |
| OpenCode | `~/.local/share/opencode/` | SQLite |
| Factory Droid | `~/.factory/sessions/` | JSONL + JSON |
| Cursor CLI | `~/.cursor/projects/*/agent-transcripts/` | JSONL |

---

## Installation

### Option 1: npx (No Install)

```bash
npx continues
```

### Option 2: Global Install

```bash
npm install -g continues
```

Both `continues` and `cont` commands work after global install.

---

## Quick Start

### Interactive Mode (Default)

```bash
continues
```

This opens a TUI to:
1. Browse/filter sessions across all tools
2. Select a session to resume
3. Choose target tool for handoff

### List All Sessions

```bash
continues list
```

### Resume Specific Session

```bash
# Resume latest Claude session in Gemini
continues resume abc123 --in gemini

# Resume specific session by ID
continues resume <session-id>
```

### Quick Resume (Native)

```bash
continues claude        # Latest Claude session
continues codex 3       # 3rd most recent Codex session
continues copilot       # Latest Copilot session
continues gemini 2      # 2nd most recent Gemini session
```

---

## Requirements

- **Node.js 22+** — Uses built-in `node:sqlite` for OpenCode parsing
- At least one of the supported AI coding tools installed

Check Node version:
```bash
node --version
```

---

## Usage with Vibe-Coding Template

### Session Handoff Workflow

1. **End Session** — When finishing a session, optionally run `continues` to prepare for handoff
2. **Start Session** — When starting a new session in a different tool, use `continues` to inject previous context
3. **Cross-tool Work** — Switch tools mid-project without losing context

### Example Workflow

```bash
# You're working in Claude Code, hit rate limit
# Save session and prepare for handoff:
continues

# Later, continue in Gemini CLI:
continues resume <session-id> --in gemini
```

---

## Integration with Template Skills

### End Session (Optional)

When using the end-session skill, you can optionally:
1. Run `continues` to make session discoverable
2. Note the session ID in handoff notes

### Start Session (Optional)

When using the start-session skill, you can optionally:
1. Run `continues list` to find previous sessions
2. Use `continues resume <id> --in <tool>` to inject context

See `.agent/workflows/session-handoff.md` for detailed workflow.

---

## Output Formats

### List Output

```
Found 894 sessions (showing 5):

[claude]   2026-02-19 05:28  dev-test/SuperCmd     SSH tunnel config debugging         84a36c5d
[copilot]  2026-02-19 04:41  migrate-to-tauri      Copy Presets From Electron          c2f5974c
[codex]    2026-02-18 23:12  cli-continues         Fix OpenCode SQLite parser          a1e90b3f
[gemini]   2026-02-18 05:10  my-project            Tauri window management             96315428
[opencode] 2026-02-14 17:12  codex-session-picker  Where does Codex save JSON files    ses_3a2d
```

### JSON Output

```bash
continues list --json
continues list --jsonl -n 10
```

---

## Session Index

- **Cached at**: `~/.continues/sessions.jsonl`
- **Auto-refresh**: 5 minute TTL
- **Force rebuild**: `continues rebuild`

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `continues` | Interactive TUI picker |
| `continues list` | List all sessions |
| `continues list --source claude` | Filter by tool |
| `continues resume <id>` | Resume by session ID |
| `continues resume <id> --in <tool>` | Cross-tool handoff |
| `continues scan` | Show session discovery stats |
| `continues rebuild` | Force-rebuild session index |
| `continues <tool> [n]` | Quick-resume Nth session |

---

## Troubleshooting

### No sessions found

```bash
# Rebuild index
continues rebuild
```

### Node version error

```bash
# Install Node.js 22+
nvm install 22
nvm use 22
```

### Session not appearing

- Check that the AI tool has been used at least once
- Verify session directory exists (see table above)
- Run `continues scan` to see discovered sessions

---

## Why Use It?

Have you ever:
- Hit a rate limit mid-debugging session?
- Needed to switch tools for a specific capability?
- Lost context when continuing in a different CLI?

`cli-continues` solves this by extracting your conversation history, file changes, and AI reasoning — then injecting it into your target tool.

---

## Links

- GitHub: [yigitkonur/cli-continues](https://github.com/yigitkonur/cli-continues)
- npm: [continues](https://www.npmjs.com/package/continues)
- Template context: `.agent/CONTEXT.md`
- Session handoff workflow: `.agent/workflows/session-handoff.md`
