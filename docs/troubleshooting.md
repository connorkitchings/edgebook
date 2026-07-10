# Troubleshooting Guide

Quick reference for diagnosing and resolving common issues.

---

## Triage Matrix

| Issue Type | Route To | First Diagnostic | Common Fix |
|------------|----------|------------------|------------|
| Install/env errors | DevEx | Python version? UV installed? | `uv sync` |
| Import errors | DevEx | Check pyproject.toml | `uv sync` |
| Lint failures | DevEx | Run with --fix? | `uv run ruff check . --fix` |
| Test failures | Feature/Core | Run with -vv? | `uv run pytest -vv -k <pattern>` |
| CI-only failures | DevEx | Secrets configured? | Check workflow logs |
| Data issues | DataOps | Schema changes? | Verify data paths |
| API errors | Web/UI | Rate limits? Auth? | Check logs and config |
| Performance | Feature/Core | Profiling done? | Profile before optimizing |
| Context drift | Any | Session log stale? | Clear + resume from logs |
| Stuck > 30min | Any | Documented blockers? | Create handoff packet |

---

## Common Issues

### Environment Issues

**Problem: `ModuleNotFoundError`**
```bash
# Solution: Sync dependencies
uv sync

# If still failing, check pyproject.toml dependencies
cat pyproject.toml | grep -A 10 "dependencies"
```

**Problem: `uv: command not found`**
```bash
# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Problem: Python version mismatch**
```bash
# Solution: Check required version
python --version
# Should be >= 3.10

# Install correct version if needed
uv python install 3.12
```

---

### Code Quality Issues

**Problem: Linting fails**
```bash
# Auto-fix most issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# View specific errors
uv run ruff check . --output-format=full
```

**Problem: Pre-commit hooks fail**
```bash
# Install hooks (first time)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Skip hooks if necessary (not recommended)
git commit --no-verify
```

---

### Test Issues

**Problem: Tests fail locally**
```bash
# Run with verbose output
uv run pytest -vv

# Run specific test file
uv run pytest tests/test_example.py

# Run tests matching pattern
uv run pytest -k "test_pattern"

# Re-run last failed tests
uv run pytest --lf

# Show print statements
uv run pytest -s
```

**Problem: Tests pass locally but fail in CI**
```bash
# Check for:
# 1. Missing dependencies in pyproject.toml
# 2. Environment variables not set in CI
# 3. Different Python version
# 4. Timing/race conditions

# Reproduce CI environment locally
uv sync
uv run pytest
```

---

### Git Issues

**Problem: Accidentally on main branch**
```bash
# Stash your changes
git stash

# Create feature branch
git checkout -b feat/<name>

# Restore your changes
git stash pop
```

**Problem: Merge conflicts**
```bash
# Check which files have conflicts
git status

# Open conflicted files and resolve
# Look for <<<<<<< HEAD markers

# After resolving, mark as resolved
git add <resolved-files>
git commit
```

**Problem: Need to undo last commit**
```bash
# Undo commit but keep changes
git reset --soft HEAD~1

# Undo commit and discard changes (CAREFUL!)
git reset --hard HEAD~1
```

---

### Documentation Issues

**Problem: MkDocs build fails**
```bash
# Check for syntax errors in markdown
mkdocs build --strict

# Validate navigation in mkdocs.yml
cat mkdocs.yml

# Common issues:
# - Broken internal links
# - Missing files referenced in nav
# - YAML syntax errors
```

**Problem: Broken links in docs**
```bash
# Use link checker script
python scripts/check_links.py

# Manually check specific doc
cat docs/<file>.md | grep -E "\[.*\]\(.*\)"
```

---

### Session Issues

**Problem: Context drift during long session**
1. Pause and create session log documenting progress
2. Clear chat history
3. Resume from session log + `.agent/CONTEXT.md`
4. Load only files needed for current task

**Problem: Lost track of what to do next**
1. Read last session log in `session_logs/`
2. Check `docs/implementation_schedule.md`
3. Review `.agent/CONTEXT.md` for current priorities

**Problem: Stuck for > 30 minutes**
1. Document blockers in session log
2. Create handoff packet with context
3. Flag for human review
4. Consider alternate approaches or escalate to different role

---

### AI Agent Issues

**Problem: Agent loading too much context**
- Use tiered loading (see `AGENTS.md`)
- Load Tier 1 only, fetch Tier 2/3 on-demand
- Check context budget (aim for ≤10k tokens per session)

**Problem: Agent making changes without approval**
- Review permission settings
- Ensure planning phase completes before implementation
- Use `.agent/skills/start-session/SKILL.md` workflow

**Problem: Agent not following project rules**
- Verify critical rules in `AGENTS.md` are up-to-date
- Check `.agent/CONTEXT.md` has current constraints
- Update project-specific "NEVER" rules section

---

## Escalation Guidelines

### When to Escalate

- Security issues (credentials exposed, vulnerabilities)
- Data loss or corruption risks
- Breaking changes to public APIs
- Production deployment issues
- Unable to resolve after 2 serious attempts
- Conflicting requirements or ambiguous specs

### How to Escalate

1. **Document thoroughly** in session log:
   - What was attempted
   - Results/errors observed
   - Debugging steps taken
   - Current state of work

2. **Create handoff packet**:
   - Clear problem statement
   - Relevant file paths and line numbers
   - Expected vs actual behavior
   - Proposed solutions considered

3. **Flag for review**:
   - Tag in session log with `⚠️ ESCALATION`
   - Update implementation schedule status
   - Notify team via appropriate channel

---

## Prevention

### Avoid Common Pitfalls

1. **Always run health check before committing**
   ```bash
   # Health check workflow
# See .agent/workflows/health-check.md for steps
   ```

2. **Create session logs consistently**
   - Use `.agent/skills/end-session/SKILL.md`
   - Document decisions and blockers
   - Update implementation schedule

3. **Follow boot order when starting sessions**
   - AGENTS.md → README.md → .agent/CONTEXT.md
   - Review last 3-5 session logs
   - Plan before implementing

4. **Respect context budget**
   - Load Tier 1 first, Tier 2/3 on-demand
   - Summarize instead of loading full files
   - Use search/grep instead of reading entire modules

5. **Branch safety**
   - Check branch before starting: `git branch`
   - Never work directly on `main`
   - Create descriptive feature branch names

---

## Setup Issues

### Problem: setup_project.py fails to update files

**Symptoms:**
- Script runs but files remain unchanged
- Permission denied errors

**Solutions:**
```bash
# Check file permissions
ls -la README.md pyproject.toml

# Make files writable
chmod +w README.md pyproject.toml .agent/CONTEXT.md

# Run setup with verbose output
python scripts/setup_project.py --verbose

# Manual fallback - edit files directly
# Template variables are documented in implementation_schedule.md
```

---

### Problem: Makefile commands not found

**Symptoms:**
- `make: command not found`
- `No rule to make target 'test'`

**Solutions:**
```bash
# Check if make is installed
which make

# Install make
# macOS:
brew install make

# Ubuntu/Debian:
sudo apt-get install build-essential

# Alternative: use uv commands directly
uv run pytest        # instead of make test
uv run ruff check .  # instead of make lint
```

---

## Testing Issues

### Problem: Coverage below 75% threshold

**Symptoms:**
- Tests pass but coverage check fails
- `Coverage failure: total of 65 is less than fail-under=75`

**Solutions:**
```bash
# Check current coverage
make test

# View HTML report
open htmlcov/index.html

# Identify uncovered code
# Look for red lines in HTML report

# Add tests for uncovered code
# Or adjust target in pyproject.toml:
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=70",  # Lower threshold temporarily
]

# Exclude specific paths from coverage
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/experimental/*",
    "*/legacy/*",
]
```

---

### Problem: Integration tests fail

**Symptoms:**
- `ModuleNotFoundError` for optional dependencies
- Import errors in test files

**Solutions:**
```bash
# Install optional dependencies
uv sync --extra data-science
uv sync --extra mlops

# Or run only unit tests
uv run pytest tests/unit/

# Skip specific test files
uv run pytest --ignore=tests/integration/

# Check fixtures exist
ls tests/fixtures/

# Verify test imports work
uv run python -c "from vibe_coding.config import Config"
```

---

## Documentation Issues

### Problem: MkDocs build fails

**Symptoms:**
- `Config value 'plugins': The "mkdocstrings" plugin is not installed`
- Navigation errors
- Missing file references

**Solutions:**
```bash
# Install docs dependencies
uv sync --extra docs

# Check mkdocstrings is installed
uv run pip list | grep mkdocstrings

# Build with verbose output
uv run mkdocs build --verbose

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))"

# Check for broken links
python scripts/validate_template.py

# Check all referenced files exist
# Look for errors like: "File not found: docs/missing_file.md"
```

---

### Problem: Template validation shows warnings

**Symptoms:**
- Yellow ⚠ warnings in validation output
- "Broken link in docs/..."

**Solutions:**
```bash
# Run validation
python scripts/validate_template.py

# Check which specific files have issues
# Warnings are often expected for templates:
# - Placeholder variables are normal (users fill them in)
# - Some documentation links may be template paths

# Fix broken links if they reference real files
grep -r "\./docs/missing" docs/

# Update mkdocs.yml navigation if files were moved
# Remove references to deleted files
```

---

## VS Code Issues

### Problem: Snippets not appearing

**Symptoms:**
- Typing prefix doesn't show snippet
- Snippets don't expand

**Solutions:**
```bash
# Verify snippets file exists
ls .vscode/vibe-coding.code-snippets

# Check JSON syntax
python -c "import json; json.load(open('.vscode/vibe-coding.code-snippets'))"

# Reload VS Code window
# Command Palette → "Developer: Reload Window"

# Check VS Code settings
# File → Preferences → Settings
# Search "snippets" and ensure enabled
```

---

## Git Integration Issues

### Problem: vibe_sync suggest shows no session logs

**Symptoms:**
- "No session logs found" error
- Empty commit message suggestions

**Solutions:**
```bash
# Check if session logs exist
ls session_logs/

# Create a session log first
uv run python scripts/vibe_sync.py end

# Check log format matches template
cat session_logs/TEMPLATE.md

# Verify log was created
ls -la session_logs/$(date +%m-%d-%Y)/

# Run suggest again
uv run python scripts/vibe_sync.py suggest
```

---

### Problem: Git operations fail during setup

**Symptoms:**
- "Failed to initialize git"
- "Failed to create branch"
- Permission denied

**Solutions:**
```bash
# Check git is installed
which git
git --version

# Check if already a git repo
ls -la .git

# Manual git initialization
git init
git checkout -b feat/initial-setup

# Check git config
git config user.name
git config user.email

# Set if missing
git config user.name "Your Name"
git config user.email "your@email.com"
```

---

## Getting Help

- **Documentation**: `docs/` directory
- **Session history**: `session_logs/` (last 3-5 logs)
- **Project context**: `.agent/CONTEXT.md`
- **Standards**: `docs/development_standards.md`
- **Checklists**: `docs/checklists.md`

If you've exhausted these resources and still blocked, document the issue thoroughly and escalate.
