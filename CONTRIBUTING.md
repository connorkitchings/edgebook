# Vibe Coding Template - Contributing Guide

> **Purpose:** Guidelines for contributing to this project.

---

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup

```bash
# Clone repository
git clone <repo-url>
cd <repo-name>

# Install dependencies
uv sync

# Run tests to verify setup
uv run pytest
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
# Never work on main
git checkout -b feat/your-feature-name
```

Branch naming conventions:
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code restructuring
- `chore/` - Maintenance

### 2. Make Changes

- Follow code style (ruff formatting)
- Write tests for new code
- Update documentation
- Keep changes focused and small

### 3. Run Quality Checks

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check .

# Run tests
uv run pytest

# Full health check
cat .agent/workflows/health-check.md
```

### 4. Create Session Log

Follow `.agent/skills/end-session/SKILL.md` to document work.

### 5. Commit and Push

```bash
# Stage changes
git add <files>

# Commit with conventional format
git commit -m "feat: add new feature

- Detailed change 1
- Detailed change 2

Refs: #issue-number"

# Push to remote
git push origin feat/your-feature-name
```

Commit types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code restructuring
- `chore:` Maintenance

### 6. Create Pull Request

- Use clear title and description
- Link to related issues
- Ensure all checks pass
- Request review

---

## Code Standards

### Python

- Use type hints
- Follow PEP 8 (enforced by ruff)
- Write docstrings for public APIs
- Keep functions focused

### Testing

- Write unit tests for logic
- Write integration tests for workflows
- Aim for >80% coverage
- Test edge cases

### Documentation

- Update README for user-facing changes
- Update docs/ for technical changes
- Use clear, concise language
- Include examples

---

## Pull Request Process

1. **Before submitting:**
   - All tests pass
   - Code formatted and linted
   - Documentation updated
   - Session log created

2. **PR description:**
   - What changed
   - Why it changed
   - How to test
   - Screenshots (if UI)

3. **Review process:**
   - Address feedback
   - Keep discussion constructive
   - Update as needed

4. **After merge:**
   - Delete branch
   - Update implementation schedule

---

## Reporting Issues

### Bug Reports

Include:
- What happened
- What you expected
- Steps to reproduce
- Environment details
- Error messages/logs

### Feature Requests

Include:
- Use case
- Proposed solution
- Alternatives considered
- Additional context

---

## Project Structure

```
.
├── src/              # Source code
├── tests/            # Test suite
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── .agent/           # AI workflows
├── session_logs/     # Session history
└── config/           # Configuration
```

---

## AI-Assisted Development

This project uses AI coding tools. When working with AI:

- Start with `.agent/skills/start-session/SKILL.md`
- End with `.agent/skills/end-session/SKILL.md`
- Create session logs for all work
- Follow skills catalog for common tasks
- Never commit directly on main

---

## Questions?

- Check `docs/` for detailed guides
- Review session logs for recent context
- Ask in issues or discussions

---

**Thank you for contributing!**
