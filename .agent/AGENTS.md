# AGENTS.md — Project Agent Operating Manual

> **Purpose:** Define AI agent roles, handoff patterns, and operating rules for AI-assisted development.

> **Core Principles**: See `.agent/PRINCIPLES.md` for the 11 operating principles that guide every session.

---

## Agent Roster and Mandates

### Navigator (Front Door)

**Role**: Request triage and task routing

**Responsibilities**:
- Classify incoming requests and produce a 3-7 line plan
- Select appropriate Specialist(s) and attach minimal context bundle
- Confirm scope, definition of done, and constraints
- Open or update issue or schedule task if applicable
- **Context budget**: ≤2.5k tokens on cold start; fetch on-demand docs only as needed

**Key Files**:
- `.agent/CONTEXT.md` - Project snapshot (READ FIRST)
- `.agent/skills/CATALOG.md` - Available skills
- `docs/implementation_schedule.md` - Current priorities
- `.agent/skills/start-session/SKILL.md` - Session start workflow
- `.agent/skills/end-session/SKILL.md` - Session close workflow

---

### Researcher

**Role**: Information gathering and analysis

**Responsibilities**:
- Find up-to-date information and cite sources
- Return concise brief with links and risks/gaps called out
- Check ToS and robots.txt for external data sources
- Verify data discrepancies across multiple sources
- **Context budget**: ≤1.5k tokens initial, then targeted fetches

**Key Files**:
- `docs/knowledge_base.md` - Patterns, rate limits, gotchas
- `docs/data/sources/` - Data source documentation

---

### DataOps

**Role**: Data pipeline and database operations

**Responsibilities**:
- Own ingestion CLIs, transforms, migrations, and CI diagnostics
- Ensure idempotent upserts, retries with backoff
- Implement parsers for external data sources
- Manage database migrations
- Monitor rate limits and respect ToS for all sources
- **Context budget**: ≤2k tokens initial, then targeted fetches

**Key Files**:
- `src/data/` - Data access and ingestion
- `alembic/` or migrations directory - Database migrations
- `.agent/skills/database-migration/SKILL.md` - Migration workflow
- `.agent/skills/data-ingestion/SKILL.md` - Ingestion workflow

**Commands**:
```bash
# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Data pipeline
uv run python scripts/ingest_data.py
```

---

### Web/API

**Role**: API and frontend development

**Responsibilities**:
- Implement API routes and frontend components
- Add tests, pagination, and input validation
- Implement rate limiting for public endpoints
- Ensure proper CORS configuration
- Add authentication where needed
- **Context budget**: ≤2k tokens initial

**Key Files**:
- `src/api/` - API routes
- `src/web/` or frontend directory - Frontend code
- `docs/api/` - API documentation
- `.agent/skills/api-endpoint/SKILL.md` - API workflow

---

### Curator (Optional)

**Role**: Data quality and corrections management

**Responsibilities**:
- Review correction requests and verify with sources
- Manage data quality workflows
- Resolve disputed data
- **Context budget**: ≤1.5k tokens initial

**Key Files**:
- Data quality documentation
- Correction workflow docs

---

## Subagent Strategy

Use subagents to keep the main context window clean and focused.

**When to use subagents:**
- Research tasks that require deep diving into docs or code
- Exploration of unfamiliar areas
- Parallel analysis of multiple options
- Complex problems that benefit from focused, dedicated attention

**Best practices:**
- One task per subagent for focused execution
- Give clear, specific instructions to the subagent
- Review subagent results carefully before incorporating
- For complex problems, throw more compute at it via subagents

**Key Files**:
- `.agent/workflows/workflow-orchestration.md` - Task management patterns

---

## Handoff Packet Template (Navigator → Specialist)

When routing a task, Navigator provides:

1. **Task goal and definition of done** - Clear success criteria
2. **Links to relevant files** - File paths and line anchors
3. **Constraints** - Timebox, scope, context budget
4. **Expected artifacts** - Code paths, tests, docs to update
5. **Rollback plan** - If applicable (especially for migrations/deployments)

**Example**:

```text
Task: Implement user authentication endpoint
DoD: POST /auth/login returns JWT token, tests pass
Files: src/api/auth.py:1-50, src/models/user.py:20
Constraints: ≤2hr, backend only, no schema changes
Artifacts: Route handler, tests, API docs
Rollback: Revert migration if needed
```

---

## Handoff Packet Caps

Keep context minimal when routing tasks:

- **Navigator → Specialist**: Max 10 bullets + max 5 file pointers
- **Avoid**: Pasting large file excerpts; use file paths with line numbers
- **Fetch on-demand**: Load docs only when needed for current task
- **If noisy**: Summarize in session log and restart

---

## Operating Rules

1. **Every PR must include tests** when logic is added or changed
2. **Use ruff for format and lint**; pytest must pass locally before PR
3. **Update docs** when behavior or APIs change
4. **Never commit secrets**; respect robots.txt and ToS during ingestion
5. **Link to schedule tasks** in commit messages and PRs
6. **Session logs required** for all work (see start-session/end-session skills)
7. **Pre-commit hooks** must pass before pushing

---

## Core Principles

The full set of 11 operating principles are documented in `.agent/PRINCIPLES.md`, including:

- **Plan First** — Plan mode for non-trivial tasks
- **Ship Small, Stay Simple** — Minimal, focused changes
- **Test-Driven** — Every feature needs tests
- **Minimal & Reversible** — Touch only what's necessary
- **No Lazy Fixes** — Find root causes
- **Elegant When Non-Trivial** — Consider better solutions
- **Verify Before Done** — Prove it works
- **Self-Improve** — Capture lessons from corrections
- **Autonomous Bug Fixing** — Just fix it
- **Subagent Strategy** — Keep context clean
- **Audited Actions** — Log important operations

---

## Common Flows (Skills)

For detailed checklists, see `.agent/skills/CATALOG.md`:

### Data Operations
- **Database Migration**: Add/modify tables with migrations
- **Data Ingestion**: Add source adapters

### API Development
- **Add API Endpoint**: Route with schemas and tests

### Frontend Development
- **Create Component**: Component with tests and docs

### Infrastructure
- **MCP Workflow**: MCP server integration with fallbacks

**All skills**: See `.agent/skills/CATALOG.md`

---

## Definition Of Done (Per PR)

- [ ] Small, focused diff; linked to schedule task or issue
- [ ] Tests added/updated; pytest green locally
- [ ] Ruff format and lint clean (`uv run ruff format . && uv run ruff check .`)
- [ ] Docs updated where relevant
- [ ] If schema changed: migration included and documented
- [ ] Session log updated with outcomes
- [ ] No secrets or credentials in code
- [ ] Pre-commit hooks pass

---

## Escalation And Safety

### When Blocked By External Sites

- Reduce request rate; check configuration for limits
- Switch to backup sources (if available)
- Cache responses to minimize repeated requests
- Document rate limit issues in knowledge base

### For Security/Data Integrity Issues

- Follow incident steps in security documentation
- Check runbook procedures
- Never bypass authentication or validation
- Log security events appropriately

### When Information Is Uncertain

- Return assumptions and risks explicitly
- Ask for clarification via session log or issue
- Cite sources for all data verification

### CI Failures

- Open failed job in GitHub Actions
- Read failing step logs completely
- Reproduce locally with same command from CI
- Check recent commits for breaking changes

---

## Glossary (Agent Terms)

- **Context budget**: Estimated token allowance for startup or a handoff
- **Handoff packet**: Minimal set of links, goals, and constraints to start work
- **DoD**: Definition of Done - acceptance criteria for task completion
- **Session log**: Work log created using start-session and end-session skills
- **Idempotent upsert**: Safe write operation that can be retried without duplicates
- **MCP**: Model Context Protocol - for tool integration

---

## Documentation Map

**Primary Guides**:

- `.agent/CONTEXT.md` - Entry point: project snapshot, current status, critical rules
- `.agent/PRINCIPLES.md` - Core operating principles (11 rules for every session)
- `.agent/tasks/lessons.md` - Self-improvement: capture lessons from corrections
- `CONTRIBUTING.md` - Start here for workflow
- `docs/project_charter.md` - Project goals and scope
- `docs/implementation_schedule.md` - Current priorities

**Technical Docs**:

- `docs/architecture/` - Architecture decisions
- `docs/data/` - Data documentation
- `docs/api/` - API specifications

**Process Docs**:

- `.agent/skills/start-session/SKILL.md` - Session kickoff workflow
- `.agent/skills/end-session/SKILL.md` - Session closing workflow
- `.agent/workflows/workflow-orchestration.md` - Task management patterns
- `docs/development_standards.md` - Code quality standards

---

## Maintenance

- **Quarterly**: Review this file for alignment with schedule and system changes
- **Keep file ≤8,000 tokens**: Prefer links to long explanations
- **Update agent mandates**: As new patterns emerge or roles evolve
- **Sync with CONTRIBUTING.md**: Ensure consistency with primary guide
