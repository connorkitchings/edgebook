# Health Check Workflow

Run pre-commit quality checks: formatting, linting, and tests.

---

## When to Use

- Before creating a commit
- Before pushing to remote
- Before creating a pull request
- As part of CI/CD pipeline

---

## Steps

### Step 1: Check Code Formatting

**Command:**
```bash
uv run ruff format .
```

**Expected Result:**
All files formatted successfully.

**If Fails:**
```bash
# Auto-fix format issues
uv run ruff format .
```

---

### Step 2: Run Linter

**Command:**
```bash
uv run ruff check .
```

**Expected Result:**
Zero errors or warnings.

**If Fails:**
```bash
# Auto-fix linting issues
uv run ruff check . --fix

# Check specific errors
uv run ruff check . --output-format=full
```

---

### Step 3: Run Tests

**Command:**
```bash
uv run pytest -q
```

**Expected Result:**
All tests pass.

**If Fails:**
```bash
# Run with verbose output
uv run pytest -vv

# Run last failed only
uv run pytest --lf

# Run specific test file
uv run pytest tests/test_specific.py -v
```

---

### Step 4: Check Git Status

**Command:**
```bash
git status
```

**Expected Result:**
All changes staged or committed.

---

## Full Script (Optional)

For automation, you can save this as a script:

```bash
#!/bin/bash
# health-check.sh

set -e  # Exit on first error

echo "🏥 Running health checks..."
echo ""

echo "📐 Checking code formatting..."
uv run ruff format .
echo "✅ Formatting complete"
echo ""

echo "🔍 Running linter..."
uv run ruff check .
echo "✅ Linting passed"
echo ""

echo "🧪 Running tests..."
uv run pytest -q
echo "✅ Tests passed"
echo ""

echo "✨ All health checks passed!"
echo ""
echo "Ready to commit."
```

---

## Validation

**Success Criteria:**
- [ ] Formatting check passes
- [ ] Linting check passes
- [ ] All tests pass
- [ ] No uncommitted changes (optional)

---

## Common Failures

### Formatting Failures
**Cause:** Code not formatted with ruff.
**Fix:** Run `uv run ruff format .`

### Linting Failures
**Cause:** Style violations or errors.
**Fix:** Run `uv run ruff check . --fix`

### Test Failures
**Cause:** Broken code or missing dependencies.
**Fix:** 
1. Check test output
2. Fix failing code
3. Run tests again

---

## Next Steps

After all checks pass:

1. Review changes: `git status`
2. Stage files: `git add <files>`
3. Commit: `git commit -m 'type: description'`
4. Push: `git push origin <branch>`

---

**Links:**
- `.agent/skills/end-session/SKILL.md` - End session workflow
- `docs/checklists.md` - Pre-commit checklist
- `docs/development_standards.md` - Code standards
