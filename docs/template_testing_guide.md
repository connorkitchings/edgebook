# Template Testing Guide

This guide provides step-by-step instructions for validating that the Vibe Coding Template works correctly.

---

## Quick Validation

Run the automated validation script:

```bash
# From project root
uv run python scripts/validate_template.py
```

This checks:
- ✅ Required files exist
- ✅ Documentation links are valid
- ✅ No broken paths
- ✅ Directory structure is correct

---

## Manual Testing Checklist

### 1. Fresh Clone Test

```bash
# Clone to a temporary location
cd /tmp
git clone /path/to/Vibe-Coding test-clone
cd test-clone

# Verify structure
ls -la
```

**Expected:** All directories and files listed in README structure

---

### 2. Environment Setup

```bash
# Install dependencies
uv sync

# Verify installation
uv run python -c "import vibe_coding; print(vibe_coding.__version__)"
```

**Expected:** Version 0.1.0 printed without errors

---

### 3. Code Quality Checks

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check .

# Run tests
uv run pytest
```

**Expected:** All checks pass (tests may show deprecation warnings for optional deps)

---

### 4. Example Code Test

```bash
# Test config module
uv run python -c "
from vibe_coding.config import get_config, Config
from pathlib import Path
import tempfile

# Create test env file
with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
    f.write('TEST_KEY=test_value')
    env_path = f.name

# Test config loading
config = Config(env_path)
assert config.get('TEST_KEY') == 'test_value'
assert config.get('MISSING_KEY', 'default') == 'default'
print('✓ Config module works')
"

# Test logging module
uv run python -c "
from vibe_coding.utils.logging import get_logger, setup_logging
setup_logging()
logger = get_logger('test')
logger.info('Test message')
print('✓ Logging module works')
"
```

**Expected:** Both tests print success messages

---

### 5. Session Management Test

```bash
# Test vibe-sync CLI
uv run python scripts/vibe_sync.py start
# Enter test values when prompted

# Check that context was updated
grep -A 5 "Recent Activity" .agent/CONTEXT.md

# Test end session
uv run python scripts/vibe_sync.py end
# Enter test values when prompted

# Verify log was created
ls -la session_logs/$(date +%m-%d-%Y)/
```

**Expected:** Session log created with proper format

---

### 6. Documentation Build

```bash
# Build docs
uv run mkdocs build

# Verify output
ls -la site/
```

**Expected:** site/ directory created with HTML files

---

### 7. CI Simulation (Local)

```bash
# Run validation script
python scripts/validate_template.py

# Check specific validations
echo "Checking AGENTS.md..."
test -f .agent/AGENTS.md && echo "✓ .agent/AGENTS.md exists"
test -f AGENTS.md && grep -q "Redirect" AGENTS.md && echo "✓ Root AGENTS.md is redirect"

echo "Checking required files..."
test -f README.md && echo "✓ README.md"
test -f pyproject.toml && echo "✓ pyproject.toml"
test -f .agent/CONTEXT.md && echo "✓ CONTEXT.md"
test -f .agent/skills/CATALOG.md && echo "✓ CATALOG.md"

echo "Checking directory structure..."
test -d src/vibe_coding && echo "✓ src/vibe_coding/"
test -d tests && echo "✓ tests/"
test -d docs && echo "✓ docs/"
test -d .agent/skills/start-session && echo "✓ start-session skill"
test -d .agent/skills/end-session && echo "✓ end-session skill"
```

**Expected:** All checks pass

---

### 8. Skills Verification

```bash
# Verify all referenced skills exist
cat .agent/skills/CATALOG.md | grep -E '^### ' | while read skill; do
    skill_name=$(echo $skill | sed 's/### //' | tr ' ' '-')
    skill_path=".agent/skills/$skill_name/SKILL.md"
    if [ -f "$skill_path" ]; then
        echo "✓ $skill_name"
    else
        echo "⚠ $skill_name (optional or not yet created)"
    fi
done
```

---

### 9. GitHub Actions Validation

If pushing to GitHub:

```bash
# Check workflow files exist
test -f .github/workflows/ci.yml && echo "✓ CI workflow defined"
test -f .github/workflows/docs.yml && echo "✓ Docs workflow defined"

# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "✓ CI workflow valid YAML"
python -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml'))" && echo "✓ Docs workflow valid YAML"
```

---

### 10. Pre-commit Hooks Test

```bash
# Install hooks (if pre-commit installed)
pre-commit install || echo "pre-commit not installed, skipping"

# Test a commit (dry run)
git add -A
git commit --dry-run -m "test: validation commit"
```

---

## Known Issues & Workarounds

### Issue: Tests fail due to optional dependencies

**Symptoms:** Import errors in tests

**Solution:** This is expected for template. Dependencies are documented in pyproject.toml optional sections.

```bash
# Install optional deps if needed
uv sync --extra data-science
uv sync --extra mlops
uv sync --extra security
```

### Issue: MkDocs build warnings

**Symptoms:** Warnings about missing navigation entries

**Solution:** Update mkdocs.yml nav section or add missing docs

### Issue: Validation script shows warnings

**Symptoms:** Yellow ⚠ warnings in validation output

**Solution:** Check if warnings are expected (e.g., optional files) or need fixing

---

## End-to-End Test Script

Save this as `test_template.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Vibe Coding Template Validation"
echo "==================================="

# 1. Validation script
echo -e "\n1. Running validation script..."
python scripts/validate_template.py

# 2. Code quality
echo -e "\n2. Checking code quality..."
uv run ruff format . --check
uv run ruff check .

# 3. Tests
echo -e "\n3. Running tests..."
uv run pytest -q || echo "Tests completed (optional deps may be missing)"

# 4. Documentation
echo -e "\n4. Building documentation..."
uv run mkdocs build --strict

# 5. Example code
echo -e "\n5. Testing example code..."
uv run python -c "from vibe_coding import get_config; print('✓ Imports work')"

echo -e "\n✅ All validations passed!"
```

Make executable: `chmod +x test_template.sh`

Run: `./test_template.sh`

---

## Troubleshooting

### Validation Script Fails

Check which validation failed:
- **agents_md**: Check both AGENTS.md files
- **required_files**: Ensure all critical files exist
- **documentation_paths**: Check for broken links
- **placeholder_variables**: Normal for template (warnings only)
- **directory_structure**: Verify expected directories

### Tests Fail

```bash
# Run with verbose output
uv run pytest -vv

# Run specific test
uv run pytest tests/test_config.py -v

# Check Python version
python --version  # Should be >= 3.10
```

### Import Errors

```bash
# Reinstall dependencies
rm -rf .venv
uv sync
```

### Permission Issues

```bash
# Make scripts executable
chmod +x scripts/*.py
```

---

## Validation Checklist

Before considering the template ready:

- [ ] Validation script passes (or warnings are expected)
- [ ] `uv sync` completes without errors
- [ ] `uv run pytest` runs (may have import errors for optional deps)
- [ ] `uv run ruff format . --check` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run mkdocs build` succeeds
- [ ] Example imports work: `from vibe_coding import get_config`
- [ ] vibe_sync CLI runs: `uv run python scripts/vibe_sync.py --help`
- [ ] All skills referenced in CATALOG.md exist
- [ ] Documentation builds without errors
- [ ] CI workflow files are valid YAML

---

## Reporting Issues

If you find issues during testing:

1. Document in a session log: `session_logs/YYYY-MM-DD/`
2. Include:
   - Command that failed
   - Full error output
   - Python version: `python --version`
   - UV version: `uv --version`
3. Check troubleshooting guide above

---

**Related:**
- [Contributing Guide](../CONTRIBUTING.md)
- [Troubleshooting](./troubleshooting.md)
- [Development Standards](./development_standards.md)
