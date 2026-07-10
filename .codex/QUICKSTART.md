# Quick Start

> **Purpose**: Essential commands for common operations. Copy-paste ready.

---

## Setup

```bash
# First time setup
uv sync

# Activate virtual environment (optional, uv handles this)
source .venv/bin/activate
```

---

## Development

```bash
# Format and lint code
uv run ruff format . && uv run ruff check .

# Run all tests
uv run pytest

# Run tests quietly
uv run pytest -q

# Run tests with verbose output
uv run pytest -vv

# Run specific test file
uv run pytest tests/test_example.py

# Run tests matching pattern
uv run pytest -k "test_pattern"
```

---

## Health Check

```bash
# Run pre-commit checks (format, lint, test)
# See .agent/workflows/health-check.md for steps
```

---

## Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build

# Documentation available at: http://127.0.0.1:8000
```

---

## Git Workflow

```bash
# Check current branch (CRITICAL - never work on main)
git branch

# Create feature branch
git checkout -b feat/<feature-name>

# Check status
git status

# Stage changes
git add <files>

# Commit with conventional commit format
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update documentation"
git commit -m "test: add test coverage"
git commit -m "refactor: improve code structure"
git commit -m "chore: maintenance tasks"

# Push to remote
git push origin <branch-name>
```

---

## Session Management

```bash
# Start a new session
# 1. Check branch: git branch
# 2. Read: .agent/CONTEXT.md
# 3. Load: .agent/skills/start-session/SKILL.md

# End a session
# 1. Create log: session_logs/YYYY-MM-DD/NN.md
# 2. Health check: See .agent/workflows/health-check.md
# 3. Load: .agent/skills/end-session/SKILL.md
```

---

## Common Tasks

```bash
# Add new dependency
uv add <package-name>

# Add dev dependency
uv add --dev <package-name>

# Remove dependency
uv remove <package-name>

# Update dependencies
uv sync

# Check outdated dependencies
uv pip list --outdated
```

### Python Examples

```python
# Fetch web content as Markdown
from vibe_coding.utils.markdown_fetcher import fetch_markdown, MarkdownFetcherConfig

# Basic usage
result = fetch_markdown("https://example.com")
print(result.content)

# With configuration
config = MarkdownFetcherConfig(method="ai", retain_images=True, timeout=60)
result = fetch_markdown("https://example.com", config)
print(f"Tokens: {result.metadata.token_count}")
print(f"Method: {result.metadata.method_used}")
```

---

## Troubleshooting

```bash
# Lint failures - auto-fix
uv run ruff check . --fix

# Import errors - sync dependencies
uv sync

# Test failures - verbose output
uv run pytest -vv

# Test failures - last failed only
uv run pytest --lf

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## Project Structure

```
Vibe-Coding/
├── .agent/              # AI session management
├── .codex/              # Quick reference (this file)
├── src/                 # Source code
├── tests/               # Test suite
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── session_logs/        # Session history
├── config/              # Configuration
└── pyproject.toml       # Dependencies and tooling
```

---

## Essential Files

- `AGENTS.md` - AI agent guidance (read first)
- `README.md` - Project overview
- `.agent/CONTEXT.md` - Current project state
- `.codex/MAP.md` - Full project tree
- `docs/implementation_schedule.md` - Current priorities
- `session_logs/` - Recent work history

---

**Keep this file updated when core commands or workflows change.**
