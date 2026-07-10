# Release Checklist Workflow

Prepare and execute a production release.

---

## When to Use

- Preparing for production deployment
- Creating a new release
- Tagging a version
- Deploying to production environment

---

## Pre-Release Checklist

### 1. Code Quality

- [ ] All tests passing
- [ ] Code coverage meets threshold
- [ ] Linting and formatting clean
- [ ] No TODO or FIXME comments
- [ ] No debug code (print statements, breakpoints)

### 2. Documentation

- [ ] README.md updated
- [ ] CHANGELOG.md updated with version notes
- [ ] API documentation updated
- [ ] Deployment docs updated
- [ ] New features documented

### 3. Database (If Applicable)

- [ ] Migrations tested locally
- [ ] Migration rollback tested
- [ ] Data migration scripts ready
- [ ] Backup strategy confirmed

### 4. Configuration

- [ ] Environment variables documented
- [ ] Production config validated
- [ ] Secrets not in code
- [ ] Feature flags configured

---

## Release Steps

### Step 1: Create Release Branch

**Purpose:** Isolate release preparation.

**Commands:**
```bash
# Create release branch
git checkout -b release/v1.2.0

# Or use version bump tool
# uv run bumpversion minor
```

---

### Step 2: Update Version

**Purpose:** Update version numbers in codebase.

**Files to Update:**
- `pyproject.toml` - version field
- `src/__init__.py` - __version__
- `README.md` - version badge
- `docs/` - version references

**Commands:**
```bash
# Update version in pyproject.toml
# Edit manually or use tool

# Commit version bump
git add .
git commit -m "chore: bump version to 1.2.0"
```

---

### Step 3: Update Changelog

**Purpose:** Document changes in this release.

**CHANGELOG.md Format:**
```markdown
## [1.2.0] - 2026-02-11

### Added
- New feature X
- New feature Y

### Changed
- Improved performance of Z

### Fixed
- Bug in authentication
- Issue with data parsing

### Deprecated
- Old API endpoint (will be removed in v2.0)
```

**Commands:**
```bash
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.2.0"
```

---

### Step 4: Final Testing

**Purpose:** Verify release is stable.

**Commands:**
```bash
# Run full test suite
uv run pytest

# Run integration tests
uv run pytest tests/integration/

# Run e2e tests (if applicable)
# uv run pytest tests/e2e/
```

**Expected Result:**
- All tests pass
- No critical issues

---

### Step 5: Merge to Main

**Purpose:** Integrate release into main branch.

**Commands:**
```bash
# Switch to main
git checkout main

# Merge release branch
git merge release/v1.2.0

# Push to remote
git push origin main
```

---

### Step 6: Create Git Tag

**Purpose:** Mark release point in git history.

**Commands:**
```bash
# Create annotated tag
git tag -a v1.2.0 -m "Release version 1.2.0"

# Push tag to remote
git push origin v1.2.0
```

---

### Step 7: Deploy to Production

**Purpose:** Deploy release to production environment.

**Deployment Methods:**

**Option A: GitHub Actions Auto-Deploy**
- Push tag triggers deployment
- Monitor GitHub Actions

**Option B: Manual Deployment**
```bash
# Deploy backend (Railway example)
railway up

# Deploy frontend (Vercel example)
vercel --prod

# Or use MCP if available
```

---

### Step 8: Verify Deployment

**Purpose:** Confirm production is working.

**Commands:**
```bash
# Check health endpoint
curl https://your-app.com/health

# Check version endpoint
curl https://your-app.com/version

# Check logs
railway logs --tail 50
```

**Verification:**
- [ ] Health check passes
- [ ] Version matches release
- [ ] No critical errors in logs
- [ ] Key features working

---

### Step 9: Post-Release

**Purpose:** Complete release process.

**Tasks:**
- [ ] Create GitHub Release (with notes)
- [ ] Notify team
- [ ] Update implementation schedule
- [ ] Archive release branch (optional)
- [ ] Monitor for issues

**Commands:**
```bash
# Create GitHub Release (CLI)
gh release create v1.2.0 \
  --title "Release v1.2.0" \
  --notes-file CHANGELOG.md

# Or delete release branch
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0
```

---

## Rollback Plan

### If Release Has Critical Issues

**Immediate Actions:**
1. **Assess severity** - Can it wait for hotfix?
2. **Communicate** - Notify team and users
3. **Rollback** - Revert to previous version
4. **Monitor** - Watch for recovery

**Rollback Commands:**
```bash
# Option 1: Rollback deployment
railway rollback <previous-deployment-id>

# Option 2: Deploy previous version
git checkout v1.1.9
railway up

# Option 3: Hotfix
# Create hotfix branch from main
# Fix issue
# Deploy as v1.2.1
```

---

## Validation

**Pre-Release:**
- [ ] All quality checks pass
- [ ] Documentation updated
- [ ] Version bumped
- [ ] Changelog updated

**Post-Release:**
- [ ] Deployed successfully
- [ ] Health checks pass
- [ ] GitHub Release created
- [ ] Team notified
- [ ] Monitoring active

---

## Emergency Hotfix

If critical bug found in production:

1. **Create hotfix branch from main:**
   ```bash
   git checkout main
   git checkout -b hotfix/critical-bug
   ```

2. **Fix the bug** (minimal change)

3. **Test fix:**
   ```bash
   uv run pytest
   ```

4. **Bump patch version (1.2.0 → 1.2.1):**
   ```bash
   # Update version in pyproject.toml
   git commit -m "fix: critical bug description"
   ```

5. **Deploy immediately:**
   ```bash
   git checkout main
   git merge hotfix/critical-bug
   git tag -a v1.2.1 -m "Hotfix v1.2.1"
   git push origin main --tags
   railway up
   ```

---

## Links

- `.agent/skills/end-session/SKILL.md` - Session close workflow
- `.agent/workflows/test-ci.md` - CI testing
- `CHANGELOG.md` - Release notes
- `.github/workflows/deploy.yml` - Deployment config

---

**Remember: Always have a rollback plan before deploying!**
