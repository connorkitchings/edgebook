---
name: context-audit
description: "Audit and optimize context loading to stay within token budgets and improve session performance."
metadata:
  trigger-keywords: "audit context, context size, optimize loading, reduce context, context budget"
  trigger-patterns: "^audit.*context, ^optimize.*loading, ^context.*budget"
---

# Context Audit Skill

Use this skill when experiencing slow sessions, context budget issues, or token limit warnings.

---

## When to Use

- Context budget exceeded warnings
- Session feels slow or unresponsive
- Loading too many files unnecessarily
- Need to optimize context for better performance

**Do NOT use when:**
- First starting a session (use start-session skill instead)
- Working on focused task with minimal context

---

## Inputs

### Required
- **Current context size**: Estimated tokens loaded
- **Session symptoms**: What feels slow or wrong

### Optional
- **Target budget**: Desired token limit (default: 10k)
- **Files accessed**: List of files loaded during session

---

## Steps

### Step 1: Measure Current Context

**What to do:**
Count tokens and files currently loaded.

**Methods:**
1. **Check session metrics:**
   - Look for token usage indicators in your AI tool
   - Note any "context budget exceeded" warnings

2. **Estimate from files:**
   ```bash
   # Count lines in recently accessed files
   find src/ tests/ -name "*.py" -type f -mtime -1 -exec wc -l {} + | tail -1
   
   # Rough token estimate (lines * 5 for Python)
   ```

3. **List loaded files:**
   Review session log to see which files were read

**Validation:**
- [ ] Have rough token count
- [ ] Know how many files were loaded
- [ ] Identified any large files (>200 lines or 10KB)

---

### Step 2: Identify Context Drift

**What to do:**
Find unnecessary context that has accumulated.

**Common sources of drift:**
1. **Old session logs:**
   - Check if logs > 5 entries were loaded
   - Archive or summarize old logs

2. **Full file reads:**
   - Did you read entire files when only a section was needed?
   - Check for `read` operations on large files

3. **Multiple versions:**
   - Are you tracking multiple branches/versions?
   - Focus on current working state only

4. **Documentation overload:**
   - Loaded full docs when quick reference would suffice?
   - Use `.codex/QUICKSTART.md` instead of full guides

**Validation:**
- [ ] Identified >3 sources of drift
- [ ] Noted files that were read unnecessarily
- [ ] Found outdated information in context

---

### Step 3: Apply Context Optimization

**What to do:**
Implement strategies to reduce context size.

**Strategy A: File Selection**
```bash
# Use grep instead of reading full files
grep -n "def process_data" src/*.py

# Read only specific sections
read src/main.py offset=100 limit=20

# Skip auto-generated files
# Don't read: __pycache__, node_modules, .venv
```

**Strategy B: Summarize Before Loading**
Instead of reading 5 old session logs:
```markdown
# Create a summary document
## Context Summary (YYYY-MM-DD)
- Completed: [List major achievements]
- Current blockers: [Any blockers]
- Next priority: [What to work on]
- Key files: [Important paths]
```

**Strategy C: Tiered Loading**
Follow the tiered approach from AGENTS.md:
1. **Tier 1** (Always): AGENTS.md, README.md, .agent/CONTEXT.md
2. **Tier 2** (As needed): Schedule, standards, specific code
3. **Tier 3** (On-demand): Full architecture, history

**Strategy D: Use Search**
```bash
# Find relevant code without loading everything
grep -r "class DataModel" src/
find . -name "*.py" -exec grep -l "import pandas" {} \;
```

**Validation:**
- [ ] Reduced files loaded by 50%+
- [ ] Using targeted reads instead of full files
- [ ] Summarized old context into brief notes

---

### Step 4: Validate Performance

**What to do:**
Test that optimizations improved performance.

**Metrics to check:**
1. **Response time:** Are AI responses faster?
2. **Token usage:** Staying within budget?
3. **Accuracy:** Does AI still have necessary context?

**Test questions:**
- "What are the current project priorities?" (should reference CONTEXT.md)
- "What's the next task to work on?" (should reference schedule)
- "Where is the config module?" (should know src/ structure)

**Validation:**
- [ ] Responses are faster (< 5 seconds for simple queries)
- [ ] No budget warnings
- [ ] AI has correct context for current work

---

### Step 5: Document Changes

**What to do:**
Record optimization decisions in session log.

**What to document:**
```markdown
## Context Optimization
**Before:**
- Loaded files: [List]
- Estimated tokens: [Number]
- Issues: [What was slow]

**Optimizations Applied:**
1. [Strategy used and result]
2. [Strategy used and result]

**After:**
- Loaded files: [List]
- Estimated tokens: [Number]
- Performance: [Improvement noted]

**Maintaining:**
- [Rule for future sessions]
```

**Validation:**
- [ ] Session log updated with optimization details
- [ ] Future sessions can learn from this audit

---

## Context Budget Guidelines

### Per-Role Budgets
- **Navigator:** ≤2.5k tokens
- **Specialist:** ≤2k tokens
- **Per-session total:** Prefer ≤10k tokens, max 50k

### Warning Signs
- Response time > 10 seconds
- "Context limit approaching" warnings
- AI asks for clarification on basic project info
- Repeated "loading file..." messages

### Optimization Targets
- **Files loaded per session:** 5-10 max
- **Session logs read:** 3-5 max
- **Documentation:** 1-2 pages at a time
- **Code files:** Only sections being modified

---

## Validation

### Success Criteria
- [ ] Context size reduced by 30% or more
- [ ] Response times improved
- [ ] No budget exceeded warnings
- [ ] Session log documents optimizations
- [ ] Clear rules for future context management

### Verification Commands
```bash
# Check for large files
find . -name "*.md" -size +10k -type f
find . -name "*.py" -size +50k -type f

# Count recent session logs
ls -1 session_logs/*/ | wc -l

# Estimate context in docs directory
du -sh docs/
```

---

## Common Mistakes

1. **Over-optimizing:** Removing too much context causes confusion
2. **Not documenting:** Future sessions repeat the same mistakes
3. **One-time fix:** Context management needs ongoing attention
4. **Ignoring warnings:** Address budget issues early, not after failure

---

## Links

- Context: `.agent/CONTEXT.md`
- Agent Guidance: `.agent/AGENTS.md`
- Start Session: `.agent/skills/start-session/SKILL.md`
- Troubleshooting: `docs/troubleshooting.md`
