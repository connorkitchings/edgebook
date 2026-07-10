# Session Logs Directory

This directory contains chronological development session logs for the project.

## Purpose

Session logs capture:
- Objectives and scope of each development session
- Work completed during the session
- Decisions made and rationale
- Issues encountered and their resolutions
- Next steps and open questions

---

## Organization

Logs are organized by date with sequential numbering:

```
session_logs/
├── README.md                    # This file
├── TEMPLATE.md                  # Template for new session logs
├── 02-11-2026/                  # Date folder (MM-DD-YYYY)
│   ├── 1 - Feature Implementation.md
│   ├── 2 - Bug Fix.md
│   └── 3 - Documentation Update.md
├── 02-12-2026/
│   ├── 1 - Testing Session.md
│   └── 2 - Code Review.md
└── 02-13-2026/
    └── 1 - Refactoring.md
```

### Naming Convention

**Folders**: `MM-DD-YYYY` format
- Example: `02-11-2026` for February 11, 2026
- Sorts chronologically
- Easy to find recent sessions

**Files**: `N - Title.md` format
- `N` = Sequential session number for that day (1, 2, 3...)
- `Title` = Concise description of session focus
- Space-dash-space separator for readability

**Examples:**
- `1 - Feature Implementation.md`
- `2 - Bug Fix Database Migration.md`
- `3 - Documentation Update.md`

---

## Usage

### Creating Session Logs

Session logs should be created for every development session:

1. **Start session**: Follow `.agent/skills/start-session/SKILL.md`
2. **During work**: Document decisions and issues
3. **End session**: Follow `.agent/skills/end-session/SKILL.md`
4. **Create log**: Use `TEMPLATE.md` as starting point

### Workflow

**At session start:**
```bash
# 1. Check current branch
git branch

# 2. Read context
cat .agent/CONTEXT.md

# 3. Review recent logs
ls -lt session_logs/*/
```

**During session:**
- Document key decisions as you make them
- Note blockers or issues immediately
- Track which files you modify

**At session end:**
```bash
# 1. Create today's folder if needed
mkdir -p session_logs/$(date +%m-%d-%Y)

# 2. Copy template
cp session_logs/TEMPLATE.md "session_logs/$(date +%m-%d-%Y)/N - Title.md"

# 3. Fill in template

# 4. Run health check
sh .agent/workflows/health-check.sh
```

---

## Why Session Logs?

Session logs provide:
- **Continuity**: Next session knows where to start
- **Accountability**: Clear record of what was done
- **Learning**: Document decisions and their outcomes
- **Debugging**: Trace when issues were introduced
- **Handoffs**: Transfer context between team members or AI assistants
- **History**: Searchable record of project evolution

---

## Best Practices

### Content
- **TL;DR first**: Quick summary (≤5 lines) for scanning
- **Be specific**: Include file paths and line numbers
- **Document "why"**: Explain decisions, not just changes
- **Note unresolved items**: Questions for next session
- **Tag appropriately**: Use consistent tags for filtering

### Maintenance
- Create log at end of **every** session (use end-session skill)
- Keep logs focused on one session's work
- If session spans multiple days, create multiple logs
- Archive old logs periodically (older than 90 days)

### Searching
```bash
# Find logs mentioning specific term
grep -r "database migration" session_logs/

# List all logs from date range
ls session_logs/02-*-2026/

# Find logs with specific tag
grep -r "tags.*feature" session_logs/

# Show most recent 5 logs
find session_logs -name "*.md" ! -name "README.md" ! -name "TEMPLATE.md" -type f | sort -r | head -5
```

---

## Integration with Workflow

Session logs integrate with:
- **Start session skill**: Reviews last 3-5 logs for context
- **End session skill**: Creates log based on template
- **Implementation schedule**: Links tasks to session logs
- **Git commits**: Reference session logs in commit messages
- **PR descriptions**: Link to relevant session logs

---

## Tips for AI Assistants

When working with session logs:
1. **Always read last 3-5 logs** when starting session
2. **Create log at session end** using end-session skill
3. **Document handoff notes** for next session
4. **Link to implementation schedule** tasks
5. **Tag appropriately** for easy filtering

**Remember**: Session logs are for continuity, not perfection. Better to have a rough log than no log.
