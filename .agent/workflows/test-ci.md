# Test CI Workflow

Run continuous integration tests locally before pushing to ensure CI will pass.

---

## When to Use

- Before pushing to remote
- Before creating a pull request
- After making significant changes
- When CI is failing and debugging locally

---

## Steps

### Step 1: Clean Environment

**Purpose:** Ensure no stale cache or dependencies.

**Commands:**
```bash
# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Sync dependencies
uv sync
```

---

### Step 2: Run Full Test Suite

**Purpose:** Verify all tests pass in clean environment.

**Commands:**
```bash
# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Or run without coverage for speed
uv run pytest -q
```

**Expected Result:**
- 100% of tests pass
- Coverage meets project threshold (if applicable)

---

### Step 3: Run Linting and Formatting

**Purpose:** Ensure code meets style standards.

**Commands:**
```bash
# Check formatting
uv run ruff format . --check

# Run linter
uv run ruff check .

# Type checking (if using mypy)
# uv run mypy src/
```

**Expected Result:**
- No formatting issues
- No linting errors
- No type errors (if applicable)

---

### Step 4: Security Scan (Optional)

**Purpose:** Check for security vulnerabilities.

**Commands:**
```bash
# Bandit security scan (if configured)
uv run bandit -r src/

# Safety check (if configured)
# uv run safety check
```

**Expected Result:**
- No high-severity security issues

---

### Step 5: Check Documentation

**Purpose:** Ensure docs build correctly.

**Commands:**
```bash
# Build docs (if using mkdocs)
mkdocs build --strict

# Or check for broken links
# python scripts/check_links.py
```

**Expected Result:**
- Docs build without errors
- No broken internal links

---

### Step 6: Verify Git Status

**Purpose:** Ensure all changes are committed.

**Commands:**
```bash
# Check for uncommitted changes
git status

# Check branch name (should be feature branch)
git branch
```

**Expected Result:**
- Working directory clean
- On feature branch (not main)

---

## CI Simulation Script

For full CI simulation:

```bash
#!/bin/bash
# test-ci.sh

echo "🔄 Running CI simulation..."
echo ""

# Clean
echo "🧹 Cleaning environment..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Sync
echo "📦 Syncing dependencies..."
uv sync

# Format check
echo "📐 Checking formatting..."
uv run ruff format . --check

# Lint
echo "🔍 Running linter..."
uv run ruff check .

# Tests
echo "🧪 Running tests..."
uv run pytest --cov=src --cov-report=term-missing -q

# Docs (if applicable)
# echo "📚 Building docs..."
# mkdocs build --strict

echo ""
echo "✅ CI simulation complete!"
```

---

## Validation

**Success Criteria:**
- [ ] Environment cleaned
- [ ] Dependencies synced
- [ ] All tests pass
- [ ] Coverage meets threshold
- [ ] No linting errors
- [ ] No formatting issues
- [ ] Docs build (if applicable)
- [ ] On feature branch

---

## CI Failures

### If CI Fails Locally

1. **Read error message carefully**
2. **Fix issue in code**
3. **Re-run failing test:** `uv run pytest path/to/test.py::test_name -v`
4. **Run full suite again**

### Common CI Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Import errors | Missing dependency | Add to pyproject.toml |
| Test timeouts | Slow tests | Optimize or mark with @pytest.mark.slow |
| Coverage drop | New code untested | Add tests for new code |
| Linting errors | Style violations | Run `uv run ruff check . --fix` |

---

## Next Steps

After CI simulation passes:

1. Commit any final changes
2. Push to remote: `git push origin <branch>`
3. Create pull request
4. Monitor CI in GitHub Actions

---

**Links:**
- `.agent/workflows/health-check.md` - Basic health checks
- `docs/checklists.md` - Pre-merge checklist
- `.github/workflows/ci.yml` - CI configuration
