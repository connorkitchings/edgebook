# Pre-Commit Hooks

This document describes the pre-commit hooks configured for this project and how to use them.

---

## What Are Pre-Commit Hooks?

Pre-commit hooks are automated checks that run before you create a git commit. They help ensure code quality, security, and consistency by catching issues early in the development process.

---

## Installation

### First-Time Setup

```bash
# Install pre-commit hooks (run once)
pre-commit install

# Verify installation
pre-commit --version
```

**Note:** If you don't have `pre-commit` installed globally, you can add it as a dev dependency:

```bash
uv add --dev pre-commit
```

---

## Configured Hooks

The `.pre-commit-config.yaml` file defines the following checks:

### 1. **ruff** (Linting & Formatting)
- **Purpose:** Fast Python linter and code formatter
- **What it checks:**
  - Code style issues
  - Import sorting
  - Common programming errors
- **Auto-fixes:** Most issues can be auto-fixed with `--fix`

### 2. **bandit** (Security)
- **Purpose:** Find common security issues in Python code
- **What it checks:**
  - Hardcoded passwords
  - Insecure cryptographic functions
  - SQL injection vulnerabilities
  - And more...

### 3. **safety** (Dependency Security)
- **Purpose:** Check for known security vulnerabilities in dependencies
- **What it checks:**
  - Python packages with CVEs
  - Outdated dependencies with known issues

---

## Usage

### Automatic (Recommended)

Once installed, hooks run automatically when you run `git commit`:

```bash
git add .
git commit -m "feat: add new feature"
# Hooks run automatically here
```

### Manual Run

You can run hooks manually on all files:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

### Running on Staged Files Only

```bash
pre-commit run
```

---

## Common Scenarios

### Scenario 1: Hook Failed but Auto-Fixed Issues

If a hook failed but auto-fixed some issues:

```bash
# Stage the auto-fixed files
git add <fixed-files>

# Try committing again
git commit -m "feat: add new feature"
```

### Scenario 2: Hook Failed - Manual Fix Required

If a hook failed and requires manual intervention:

```bash
# Read the error message carefully
# Fix the issues
# Stage changes
git add .
git commit -m "feat: add new feature"
```

### Scenario 3: Skip Hooks (Not Recommended)

**⚠️ WARNING:** Only skip hooks in emergencies or when you know what you're doing.

```bash
git commit --no-verify -m "feat: add new feature"
```

### Scenario 4: Update Hooks

Update hook versions to latest:

```bash
pre-commit autoupdate
```

---

## Troubleshooting

### Hook is Slow

If hooks are taking too long:

1. Run specific hooks only: `pre-commit run ruff`
2. Check if `uv` dependencies are cached
3. Consider running hooks only on changed files: `pre-commit run`

### Hook Not Found

If you get "hook not found" errors:

```bash
# Reinstall hooks
pre-commit install --force

# Or clean and reinstall
rm -rf ~/.cache/pre-commit
pre-commit install
```

### Import Errors in Hooks

If hooks report import errors:

```bash
# Sync dependencies
uv sync

# Reinstall hooks
pre-commit clean
pre-commit install
```

---

## Customization

### Adding New Hooks

Edit `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.5.0
  hooks:
    - id: trailing-whitespace
    - id: end-of-file-fixer
    - id: check-yaml
```

### Disabling Hooks Temporarily

In a specific commit message:

```bash
git commit -m "feat: add new feature

skip-checks: true"
```

Or use the `--no-verify` flag (emergency only).

---

## CI Integration

Pre-commit hooks are also run in CI to ensure consistency:

```yaml
# In GitHub Actions
- name: Run pre-commit
  run: pre-commit run --all-files
```

---

## Best Practices

1. **Always install hooks** on a new clone
2. **Don't skip hooks** unless absolutely necessary
3. **Fix issues immediately** when hooks fail
4. **Keep hooks updated** with `pre-commit autoupdate`
5. **Document custom hooks** in this file

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `pre-commit install` | Install hooks in this repo |
| `pre-commit run` | Run on staged files |
| `pre-commit run --all-files` | Run on all files |
| `pre-commit run <hook-id>` | Run specific hook |
| `pre-commit autoupdate` | Update hook versions |
| `pre-commit clean` | Clean hook cache |
| `git commit --no-verify` | Skip hooks (emergency) |

---

**Related:**
- [Development Standards](./development_standards.md)
- [Quality Gates](./checklists.md)
- [Troubleshooting Guide](./troubleshooting.md)
