# Development Standards & Workflow

This document provides comprehensive standards, workflows, and best practices for development
in the Vibe Coding System. It consolidates coding standards, review processes, and operational
workflows into a single reference.

> 📚 For a high-level overview and entry point to all documentation, see [README.md](../README.md).

## Core Principles

- **Keep It Lean:** Focus on a few core, high-signal documents
- **Short Sprints:** Maintain momentum with weekly or bi-weekly cycles
- **Context Discipline:** Only provide relevant documents to focus AI collaboration
- **User-Centric:** Test with real users early and often
- **AI as Co-Pilot:** Use AI for generation, review, and ideation, but always validate its output
- **Continuous Documentation:** Documentation preserves context and decisions

## Idempotence & Data Safety

- **Idempotence is Mandatory:**
  - Migrations MUST check for existence before creating tables/columns/indexes.
  - Ingestion scripts MUST be re-runnable without duplicating data (use `upsert` or `merge`).
- **Data Safety:**
  - ALWAYS backup before destructive operations.
  - Never run `drop_all` in production.

## Performance Budgets (Dev Targets)

- **API Response:** < 400ms p95 for list endpoints.
- **Ingestion:** Hourly/daily jobs must finish within 10% of their frequency window.
- **Database:** All queries in hot paths must hit an index.

## State Management (Web)

- **Prefer Server State:** Use tools like **TanStack Query** or **SWR** for data fetching.
- **Avoid Overkill:** Do not reach for Redux or complex global stores unless absolutely necessary.
- **Principle:** "Server State > Client State" keeps the frontend lean and logic in the API.

## Development Workflow

### Branch Strategy

- **Main Branch:** `main` - Production-ready code only
- **Feature Branches:** `feature/description` - Individual features or fixes
- **Hotfix Branches:** `hotfix/description` - Critical production fixes

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes following coding standards
3. Run pre-commit checklist (see [Checklists](./checklists.md))
4. Submit pull request with clear description
5. Complete code review process
6. Run pre-merge checklist
7. Merge to `main` after approval

## Code Quality Standards

### Python Standards

- **Version:** Python 3.10+
- **Formatting:** Use `ruff` for linting, formatting, and import sorting
- **Type Hints:** All function signatures must include type hints
- **Docstrings:** Use Google-style docstrings for all public modules, classes, and functions
- **Testing:** Use `pytest` with comprehensive test coverage

### Code Structure

Python files should follow this order:

1. Shebang (if applicable)
2. Module-level docstring
3. Imports (Standard Library, Third-Party, Local Application)
4. Constants
5. Functions and classes
6. `if __name__ == "__main__":` block for executable scripts

### Code Review Guidelines

#### First Pass: Understanding the Change

- **Clarity of Purpose:** Clear PR title and description
- **Related Issue:** Change linked to specific task/issue
- **Scope:** Reasonable scope, not trying to do too many things

#### Code Quality and Style

- **Readability:** Easy to understand with clear variable/function names
- **Style Guide:** Adheres to project style (ruff formatting/linting)
- **Comments:** Well-commented, especially in complex areas
- **Simplicity (KISS):** Not unnecessarily complex
- **Don't Repeat Yourself (DRY):** No duplicated code

#### Functionality and Correctness

- **Logic:** Sound logic that correctly solves the problem
- **Edge Cases:** Handles edge cases gracefully
- **Error Handling:** Robust error handling, doesn't fail silently
- **Security:** No security vulnerabilities, security tools run

#### Testing

- **Test Coverage:** New tests cover changes with adequate coverage
- **Test Quality:** Well-written, understandable tests
- **Test Types:** Unit tests for logic, integration tests for workflows
- **Performance:** No significant performance regressions

## Notebook Governance

### Standards for Jupyter Notebooks

- **Naming Convention:** `YYYY-MM-DD_descriptive-name.ipynb`
- **Structure:** Clear sections with markdown headers
- **Documentation:** Each notebook should have purpose and usage instructions
- **Version Control:** Clear outputs before committing
- **Dependencies:** Document all required packages

### Notebook Lifecycle

1. **Exploration:** Initial data exploration and hypothesis testing
2. **Analysis:** Structured analysis with clear methodology
3. **Production:** Convert stable code to modules in `/src`
4. **Archive:** Move completed notebooks to appropriate folders

## Quality Gates & Automation

### Pre-Commit Hooks

Automated checks run before each commit:

- Code formatting (ruff)
- Linting (ruff)
- Type checking (mypy)
- Security scanning (bandit)
- Dependency scanning (safety)

### Continuous Integration

All pull requests trigger:

- Automated testing suite
- Code coverage reporting
- Security vulnerability scanning
- Documentation building
- Performance benchmarking

## Documentation Standards

### Markdown Guidelines

- Use clear, descriptive headings
- Include table of contents for long documents
- Link to related documents using relative paths
- Keep lines under 100 characters
- Use code blocks with appropriate language tags

### API Documentation

- All public APIs must have comprehensive documentation
- Include examples for complex functions
- Document all parameters and return values
- Provide usage examples

## Deployment & Operations

### Environment Management

- **Development:** Local development with hot reloading
- **Staging:** Pre-production testing environment
- **Production:** Live environment with monitoring

### Monitoring & Observability

- Application performance monitoring
- Error tracking and alerting
- Resource usage monitoring
- User behavior analytics

---

*This document consolidates development standards, code review guidelines, notebook governance,
and operational workflows into a single reference for the Vibe Coding System.*
