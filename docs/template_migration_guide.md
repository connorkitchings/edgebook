# Template Migration Guide

This guide helps you adapt an existing project or understand changes between template versions.

---

## Current Template Version: v2.0.0

Check your version: `cat TEMPLATE_VERSION`

---

## What's New in v2.0.0

### ✨ New Features

#### Interactive Setup (`scripts/setup_project.py`)

**What it does:**
- Prompts for project details interactively
- Automatically replaces template variables in all files
- Creates `.gitignore` with standard patterns
- Initializes git repository (optional)
- Creates initial feature branch (optional)

**Benefit:** Reduces manual file editing from ~15 files to one command

#### Git Integration (`vibe_sync suggest`)

**What it does:**
- Analyzes your latest session log
- Generates conventional commit message suggestions
- Detects commit type (feat, fix, docs, test, refactor)
- Lists changed files from git status

**Benefit:** Consistent commit messages based on actual work done

#### Integration Tests (`tests/integration/`)

**What's included:**
- `test_config_integration.py` - Tests config with real files
- `test_logging_integration.py` - Tests logging with file output
- `test_workflow_integration.py` - Tests CLI and workflow scripts

**Benefit:** Confidence that modules work together correctly

#### Test Coverage

**What's configured:**
- 75% coverage target
- HTML reports in `htmlcov/`
- Terminal output with missing lines
- Branch coverage enabled

**Benefit:** Measurable code quality with clear gaps identified

#### Developer Experience

**New tools:**
- **Makefile** - Convenient commands (`make test`, `make lint`, etc.)
- **VS Code Snippets** - Quick patterns for config, logging, fixtures
- **.editorconfig** - Consistent formatting across editors
- **TEMPLATE_VERSION** - Track which template version you're using

**Benefit:** Faster daily development, consistent team experience

#### Enhanced Documentation

**What's new:**
- Quick Start section in Getting Started
- This Migration Guide
- Expanded Troubleshooting guide
- Pre-commit hooks documentation

**Benefit:** Easier onboarding, clearer upgrade path

---

## Adapting Existing Projects

If you have an existing project and want to adopt v2.0 features:

### Step 1: Copy New Files

```bash
# From v2.0 template
cp scripts/setup_project.py <your-project>/scripts/
cp Makefile <your-project>/
cp .vscode/vibe-coding.code-snippets <your-project>/.vscode/
cp .editorconfig <your-project>/
cp TEMPLATE_VERSION <your-project>/

# Copy test infrastructure
mkdir -p <your-project>/tests/integration
mkdir -p <your-project>/tests/fixtures
cp tests/integration/*.py <your-project>/tests/integration/
cp tests/fixtures/* <your-project>/tests/fixtures/
```

### Step 2: Update Configuration

Add to your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--cov=vibe_coding",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=75",
]

[tool.coverage.run]
source = ["src/vibe_coding"]
branch = true
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/conftest.py",
]

[dev-dependencies]
pytest-cov = ">=5.0.0"
```

### Step 3: Merge Documentation

Review these files from v2.0 and merge relevant sections:

- `docs/getting_started.md` - Quick Start section
- `docs/template_testing_guide.md` - New file (optional)
- `docs/tools/pre_commit_hooks.md` - New file (optional)

### Step 4: Update vibe_sync.py

Add the `suggest` command to your existing `scripts/vibe_sync.py`:

```python
@app.command()
def suggest():
    """Generate commit message from session log."""
    # Copy implementation from v2.0 template
```

### Step 5: Run Setup (Optional)

If your project was created from an older template version:

```bash
# Backup first
cp -r <your-project> <your-project>-backup

# Run setup script
python scripts/setup_project.py

# Review changes carefully
git diff
```

**⚠️ Warning:** The setup script will modify project files. Review changes before committing.

---

## Version History

### v2.0.0 - 2026-02-11

**Major Features:**
- Interactive setup script
- Git integration for commit messages
- Integration test suite
- Test coverage reporting (75% target)
- Makefile with convenient commands
- VS Code snippets
- EditorConfig
- Template versioning
- Enhanced documentation

**Improvements:**
- Consolidated duplicate AGENTS.md files
- Fixed health-check path references
- Aligned template variables
- Standardized version references (3.10+)

### v1.x.x - Earlier Versions

**Core Template:**
- Initial template structure
- Basic skills (start-session, end-session)
- Documentation framework
- CI/CD workflows
- Session logging

---

## Breaking Changes

### From v1.x to v2.0

**None** - v2.0 is fully backward compatible. Existing projects continue to work without changes.

**Optional Adoptions:**
- New files won't affect existing code
- New commands are additive (old commands still work)
- Coverage target is optional (won't fail existing tests)

---

## FAQ

### Q: Do I need to upgrade my existing project?

**A:** No. v2.0 features are optional improvements. Your existing project will continue to work.

Upgrade if you want:
- Easier project setup for new team members
- Better commit message suggestions
- Integration tests for confidence
- Convenient Makefile commands

### Q: Can I use v2.0 features selectively?

**A:** Yes. Each feature is independent:
- Use `setup_project.py` without adopting Makefile
- Add integration tests without coverage requirements
- Use VS Code snippets without other v2.0 features

### Q: How do I know which template version I have?

**A:** Check the `TEMPLATE_VERSION` file:
```bash
cat TEMPLATE_VERSION
# Output: v2.0.0
```

If the file doesn't exist, you have v1.x.

### Q: Will future template versions break my project?

**A:** Major versions (v2.0 → v3.0) may have breaking changes. Minor versions (v2.0 → v2.1) are additive only.

We'll document breaking changes in this guide when they occur.

---

## Getting Help

- **Template issues:** Check `docs/troubleshooting.md`
- **Migration questions:** Create issue with "migration" label
- **Feature requests:** Use GitHub discussions

---

**Last Updated:** 2026-02-11  
**Template Version:** v2.0.0
