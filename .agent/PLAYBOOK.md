# Agent Playbook

This playbook maintains the evolving knowledge, strategic constraints, and execution patterns for this repository. It acts as the dynamic memory for the Agentic Context Engineering (ACE) framework.

## [RULES]
1. **Branch Protection**: NEVER commit directly to `main`. Always check `git branch` and create a feature branch.
2. **Session Persistence**: Every session must conclude with a documented log in `session_logs/`.
3. **Mandatory Health Checks**: Code must pass `uv run ruff check .` and `uv run pytest` before any commit.
4. **Secret Zero**: Never hardcode credentials. Always utilize environment variables.
5. **Test Coverage Policy**: Every new feature requires tests. Every bug fix requires a regression test.
6. **Test Queries First**: Define representative test queries before coding to bound scope and clarify requirements.
7. **Architecture Before Code**: Always produce an architecture document first, even if you have a solution in mind. Use it to challenge and refine the AI's design.
8. **Challenge Over-Engineering**: Question every complexity addition. Simplicity is a strategic choice, not a limitation.
9. **Human Validates Before Implementation**: Explicit human checkpoint before proceeding to code generation.

## [STRATEGIES]
1. **Template Adaptation & Initialization**: When setting up a new project from this template, first execute setup scripts, adapt the Context Router (`.agent/CONTEXT.md`), and selectively prune boilerplate code (e.g., in `notebooks/` and `models/`).
2. **Multi-Tool Synergy**: Write deterministic, self-contained scripts and follow strict formatting (`ruff`) to ensure the codebase remains navigable and modifiable by any supported AI CLI (Gemini, Claude Code, Codex).
3. **Continuous Context Maintenance**: Regularly run health checks and session handoff routines to ensure that the context files accurately reflect the current state of the architecture.

## [SUCCESS_PATTERNS]
- **Markdown Ingestion**: Leverage the integrated `markdown.new` URL-to-Markdown utility for fetching clean documentation over raw web scraping.
- **Workflow Automation**: Use `uv run scripts/vibe_sync.py start|end` to correctly manage session context and logs.
- **Incremental Validation**: Run `make validate` locally before triggering CI/CD workflows to prevent noisy pipeline failures.
- **Human-AI Collaboration Loop**: Prompt → Generate → Review → Feedback → Iterate. Human remains the final arbiter at every phase.
- **Specialized Review Agents**: Use the 10 specialized review agents for thorough, focused reviews on specific aspects of code, architecture, or process.

## [REVIEW AGENTS]

### Agent Roster (Priority Order)

| # | Agent | Purpose | Trigger |
|---|-------|---------|---------|
| 1 | Planning Orchestrator | Scope, requirements, test queries | Start of any new task |
| 2 | Architecture Reviewer | Design patterns, SOLID, scalability | After planning, before code |
| 3 | Security Reviewer | Secrets, auth, injection, exposure | Before commits with security impact |
| 4 | Over-Engineering Detector | Complexity, unnecessary abstraction | During code review |
| 5 | Edge Case Challenger | Breaking scenarios, failure modes | After architecture design |
| 6 | Data Quality Reviewer | Data integrity, validation, consistency | Data-related changes |
| 7 | Testing Reviewer | Coverage, test quality, edge cases | Before any PR |
| 8 | Performance Reviewer | Bottlenecks, scaling, latency | Before release |
| 9 | Modularity Reviewer | Separation of concerns, coupling | Code organization concerns |
| 10 | Abstraction Reviewer | Interface design, encapsulation | Interface design changes |

### How to Invoke a Review Agent

1. **Select the appropriate agent** from the roster above
2. **Copy the prompt** from `.agent/VIBE_CRITIQUE_PROMPTS.md`
3. **Fill in the context** with your specific situation
4. **Submit to AI** for review
5. **Save output** to `.agent/reviews/YYYY-MM-DD/N - [Agent] Review.md`

### When to Run Reviews

**Always run:**
- Planning Orchestrator: New features/projects
- Architecture Reviewer: Significant design decisions
- Security Reviewer: Before production deployment

**Run as needed:**
- Edge Case Challenger: After architecture design
- Over-Engineering Detector: Code that feels complex
- Testing Reviewer: Before PR if coverage concerns
- Performance Reviewer: Before release
- Modularity/Abstraction Reviewers: Refactoring work

### Review Output Location

All review outputs go to:
```
.agent/reviews/YYYY-MM-DD/N - [Agent Name] Review.md
```

See `.agent/reviews/TEMPLATE.md` for output format.

### Review Status Indicators

- ✅ Pass: No issues found
- ⚠️ Warn: Minor issues, consider fixing
- ❌ Fail: Blocking issues, must fix
- ℹ️ Info: Informational, no action required
