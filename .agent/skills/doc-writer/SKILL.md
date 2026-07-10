---
name: doc-writer
description: "Create or update technical documentation following project standards."
metadata:
  trigger-keywords: "documentation, docs, readme, write docs, update docs"
  trigger-patterns: "^document, ^write docs, ^update docs, ^readme"
---

# Doc Writer Skill

Create or update technical documentation that is clear, consistent, and maintainable.

---

## When to Use

- Creating new documentation
- Updating existing docs
- Writing README files
- Documenting architecture decisions (ADRs)
- Creating API documentation

**Do NOT use when:**
- Just fixing typos (edit directly)
- Writing code comments (do inline)
- Creating one-off notes (use session logs)

---

## Inputs

### Required
- Document type: README, ADR, API docs, etc.
- Audience: Who will read this?
- Purpose: What should they learn/do?

### Optional
- Related docs: Links to existing documentation
- Examples: Code samples to include
- Diagrams: Visual aids needed

---

## Steps

### Step 1: Determine Document Type

**What to do:**
Choose the appropriate template and location.

**Document Types:**

| Type | Location | Purpose |
|------|----------|---------|
| README | Project/component root | Overview and quickstart |
| ADR | `docs/architecture/adr/` | Architecture decisions |
| API Doc | `docs/api/` | Endpoint documentation |
| Guide | `docs/guides/` | How-to instructions |
| Knowledge Base | `docs/knowledge_base.md` | Patterns and gotchas |
| Project Brief | `docs/project_brief.md` | Project overview |
| Implementation Schedule | `docs/implementation_schedule.md` | Task tracking |

### Step 2: Apply Template

**What to do:**
Use the appropriate template for consistency.

**README Template:**
```markdown
# Project/Component Name

> One-line description

## Overview

Brief description of what this is and why it exists.

## Quick Start

### Prerequisites
- Requirement 1
- Requirement 2

### Installation
```bash
# Installation commands
```

### Usage
```bash
# Basic usage
```

## Documentation

- [Link to detailed docs](docs/)
- [API Reference](docs/api/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

[License Type](LICENSE)
```

**ADR Template:**
```markdown
# ADR-XXX: Title

## Status
- Proposed / Accepted / Deprecated / Superseded by ADR-YYY

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing or have agreed to implement?

## Consequences
What becomes easier or more difficult to do?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Drawback 1
- Drawback 2

## Alternatives Considered

### Alternative 1: Name
Description and why it was rejected.

### Alternative 2: Name
Description and why it was rejected.

## References
- [Link 1]()
- [Link 2]()
```

**Guide Template:**
```markdown
# Guide: Topic

## Overview
What this guide covers and who it's for.

## Prerequisites
What you need before starting.

## Steps

### Step 1: Title
Description and commands.

### Step 2: Title
Description and commands.

## Verification
How to verify it worked.

## Troubleshooting
Common issues and solutions.

## Next Steps
Where to go from here.
```

### Step 3: Write Content

**What to do:**
Write clear, concise content following standards.

**Writing Standards:**

1. **Clear Headings**: Use descriptive headings (not just "Overview")
2. **Short Paragraphs**: 2-3 sentences max per paragraph
3. **Bullet Points**: Use lists for multiple items
4. **Code Blocks**: Use fenced code blocks with language tags
5. **Links**: Use relative links to other docs
6. **Examples**: Include concrete examples

**Example - Good vs Bad:**

Bad:
```markdown
This function does stuff with data.
```

Good:
```markdown
The `process_data()` function validates and transforms raw data:

- **Validates**: Checks required fields and data types
- **Transforms**: Converts dates to ISO format
- **Returns**: Cleaned data dictionary

Example:
```python
result = process_data({"date": "01/01/2026", "value": 100})
# Returns: {"date": "2026-01-01", "value": 100}
```
```

### Step 4: Add Cross-References

**What to do:**
Link to related documentation.

**Pattern:**
```markdown
See also:
- [Database Schema](database_schema.md) for table definitions
- [API Reference](../api/endpoints.md) for usage examples
- [Related ADR](../adr/adr-001-database-choice.md) for context
```

### Step 5: Review and Update

**What to do:**
Review for completeness and update related docs.

**Review Checklist:**
- [ ] All sections filled
- [ ] Links work
- [ ] Code examples tested
- [ ] No typos
- [ ] Consistent with other docs

**Update Related Docs:**
- Update table of contents if exists
- Add link from overview docs
- Update implementation schedule if applicable

---

## Validation

### Success Criteria
- [ ] Follows appropriate template
- [ ] All sections complete
- [ ] Links to related docs
- [ ] Code examples tested
- [ ] Audience-appropriate level
- [ ] Consistent terminology

### Verification
```bash
# Check links
python scripts/check_links.py

# Preview markdown
cat docs/your_file.md | less

# Build docs site (if using mkdocs)
mkdocs serve
```

---

## Rollback

### If Documentation is Wrong

1. Create correction task in implementation schedule
2. Update document with correct info
3. Note correction in session log
4. Notify team if others reference the doc

---

## Common Mistakes

1. **No audience consideration**: Write for your reader
2. **Outdated code examples**: Always test examples
3. **Missing context**: Explain why, not just what
4. **Wall of text**: Use formatting to break up content
5. **Broken links**: Check all links before committing
6. **Inconsistent terms**: Use glossary terms consistently

---

## Related Skills

- **Test Writer**: For documenting test patterns
- **API Endpoint**: For API documentation
- **Start Session**: For session log documentation

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **Documentation Guide**: `docs/documentation_guide.md`
- **Glossary**: `docs/glossary.md`

---

## Examples

### Example 1: Architecture Decision Record

**Scenario:** Documenting choice of PostgreSQL over MongoDB.

**Key Sections:**
- Context: Need ACID transactions and complex queries
- Decision: Use PostgreSQL with SQLAlchemy ORM
- Consequences: Better consistency, need migration system

### Example 2: API Endpoint Documentation

**Scenario:** Documenting new user authentication endpoint.

**Content:**
- Endpoint URL and method
- Request/response schemas
- Error codes and examples
- Authentication requirements

---

**Remember: Good documentation saves time for everyone!**
