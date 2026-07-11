# Skills Catalog

> **Purpose**: Index of all available skills for common development tasks. Skills are reusable workflows with clear contracts.

---

## Core Session Skills

### start-session
**Path**: `.agent/skills/start-session/SKILL.md`
**Purpose**: Initialize a new development session safely
**Triggers**: "start", "kickoff", "begin", "new task", "hello"
**Outputs**: Planning document with roadmap options
**Use when**: Starting any new development session

### end-session
**Path**: `.agent/skills/end-session/SKILL.md`
**Purpose**: Close session properly with logging and handoff
**Triggers**: "end", "close", "finish", "wrap up", "done"
**Outputs**: Session log, health check results, handoff notes
**Use when**: Completing any development session

---

## Development Skills

### database-migration
**Path**: `.agent/skills/database-migration/SKILL.md`
**Purpose**: Create and apply database migrations safely using Alembic
**Triggers**: "migration", "schema change", "database update", "alembic"
**Outputs**: Migration file, rollback plan, test verification
**Use when**: Modifying database schema, adding tables/columns

### data-ingestion
**Path**: `.agent/skills/data-ingestion/SKILL.md`
**Purpose**: Implement data ingestion adapters for external sources
**Triggers**: "ingestion", "data source", "adapter", "etl", "pipeline"
**Outputs**: Ingestion adapter, validation logic, CLI script
**Use when**: Adding new data sources, building ETL pipelines

### api-endpoint
**Path**: `.agent/skills/api-endpoint/SKILL.md`
**Purpose**: Create new API endpoint with validation and tests
**Triggers**: "new endpoint", "API route", "create endpoint", "fastapi", "flask"
**Outputs**: Route handler, schemas, tests, API documentation
**Use when**: Adding REST API endpoints

### doc-writer
**Path**: `.agent/skills/doc-writer/SKILL.md`
**Purpose**: Create or update technical documentation
**Triggers**: "documentation", "docs", "readme", "write docs", "update docs"
**Outputs**: Documentation file following project standards
**Use when**: Writing README, ADRs, guides, or API docs

### test-writer
**Path**: `.agent/skills/test-writer/SKILL.md`
**Purpose**: Write effective tests following best practices
**Triggers**: "test", "testing", "pytest", "unit test", "integration test"
**Outputs**: Test file with fixtures and comprehensive coverage
**Use when**: Adding tests for features or bug fixes

### mcp-workflow
**Path**: `.agent/skills/mcp-workflow/SKILL.md`
**Purpose**: Use MCP servers with fallback CLI commands
**Triggers**: "mcp", "deployment", "deploy", "railway", "vercel"
**Outputs**: Deployment commands or MCP operations
**Use when**: Deploying to cloud platforms, managing infrastructure

---

## Utility Skills

### context-audit
**Path**: `.agent/skills/context-audit/`
**Purpose**: Audit and optimize context loading
**Triggers**: "audit context", "context size", "optimize loading"
**Outputs**: Context usage report, optimization recommendations
**Use when**: Context budget is exceeded or session is slow

### web-init
**Path**: `.agent/skills/web-init/`
**Purpose**: Initialize web project structure
**Triggers**: "init web", "create web app", "setup frontend"
**Outputs**: Web project scaffold
**Use when**: Starting new web project

---

## Workflow References

### health-check
**Path**: `.agent/workflows/health-check.md`
**Purpose**: Run pre-commit quality checks
**Triggers**: "health check", "validate", "pre-commit"
**Use when**: Before creating commits or PRs

### test-ci
**Path**: `.agent/workflows/test-ci.md`
**Purpose**: Run CI tests locally before pushing
**Triggers**: "test ci", "ci simulation", "pre-push"
**Use when**: Before pushing to remote, debugging CI failures

### release-checklist
**Path**: `.agent/workflows/release-checklist.md`
**Purpose**: Prepare and execute production releases
**Triggers**: "release", "deploy production", "create release"
**Use when**: Preparing for production deployment

---

## How to Use Skills

### 1. Discover Available Skills
Browse this catalog to find skills matching your task.

### 2. Load Skill Documentation
Read the skill's SKILL.md file to understand:
- When to use it
- What inputs it needs
- What outputs it produces
- Step-by-step process

### 3. Execute Skill Contract
Follow the skill's documented steps exactly. Skills are designed to be:
- **Repeatable**: Same inputs → same outputs
- **Testable**: Clear success criteria
- **Composable**: Can be chained together

### 4. Document Skill Usage
In your session log, note which skills were used and any deviations from the standard process.

---

## Creating New Skills

When creating a new skill:

1. **Identify Repeated Pattern**: Is this task done frequently?
2. **Define Clear Contract**: Inputs, outputs, success criteria
3. **Create Skill Directory**: `.agent/skills/<skill-name>/`
4. **Write SKILL.md**: Use frontmatter and clear sections
5. **Add to Catalog**: Document triggers and purpose
6. **Test Skill**: Verify it works in multiple contexts

**Skill template:**
```markdown
---
name: skill-name
description: "Brief description"
metadata:
  trigger-keywords: "keyword1, keyword2"
  trigger-patterns: "^pattern1, ^pattern2"
---

# Skill Name

## When to Use
## Inputs
## Steps
## Validation
## Common Mistakes
## Links
```

---

## Skill Maintenance

Skills should be:
- **Updated** when workflows change
- **Deprecated** when no longer needed
- **Versioned** when major changes occur
- **Tested** regularly to ensure accuracy

**Ownership**: Skills are maintained by the team. Anyone can propose updates via PR.

---

## Links

- Context: `.agent/CONTEXT.md`
- Agent guidance: `AGENTS.md`
- Start session: `.agent/skills/start-session/SKILL.md`
- End session: `.agent/skills/end-session/SKILL.md`
- Health check: `.agent/workflows/health-check.md`

---

**Skills are tools. Use them to maintain consistency and quality.**
