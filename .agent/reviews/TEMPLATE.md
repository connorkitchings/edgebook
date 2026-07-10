# Review Output Template

> Use this template for all agent review outputs. Save to `.agent/reviews/YYYY-MM-DD/N - [Agent] Review.md`

---

## Review Header

```markdown
# [Agent Name] Review — YYYY-MM-DD

## Trigger
- **Requested by**: [Human name or "Self-initiated"]
- **Scope**: [What was reviewed - e.g., "architecture document", "PR #42", "src/api/"]
- **Files examined**: [List of relevant files]
- **Context**: [Brief description of the task or change being reviewed]
```

---

## Findings (Standard Categories)

### Overall Assessment
- **Status**: ✅ Approve / ⚠️ Needs Work / ❌ Block
- **Confidence**: High / Medium / Low
- **Key concerns**: [1-3 bullet points]

### Strengths
- [What was done well]
- [What to preserve/maintain]

### Areas for Improvement
- [Issue 1 with details]
- [Issue 2 with details]

### Specific Findings

#### [Finding 1]
- **Status**: ✅ Pass / ⚠️ Warn / ❌ Fail / ℹ️ Info
- **Location**: [File path or component]
- **Details**: [Description of the finding]
- **Recommendation**: [Actionable fix or suggestion]

#### [Finding 2]
- ...

---

## Action Items

### Must Fix (Blockers)
- [ ] [Action description] — [File/Location]

### Should Fix (High Priority)
- [ ] [Action description] — [File/Location]

### Consider Fixing (Nice to Have)
- [ ] [Action description] — [File/Location]

---

## Risks Identified

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| [Risk description] | High/Med/Low | High/Med/Low | [How to address] |

---

## Questions for Human

- [Question 1]
- [Question 2]

---

## Summary

[Brief 2-3 sentence assessment of the reviewed item. Focus on:
- What works well
- Key concerns
- Recommended next steps]

---

## Metadata

```markdown
**Agent**: [Agent Name]
**Reviewer**: [Human name if applicable]
**Date**: YYYY-MM-DD
**Confidence**: High / Medium / Low
**Previous reviews**: [Link to any related prior reviews]
```

---

## Agent-Specific Categories

Depending on the agent type, use these additional sections:

### For Architecture Reviewer
```markdown
### Design Patterns
- **Pattern used**: [Name]
- **Appropriateness**: [Assessment]
- **Alternatives considered**: [Options]

### SOLID Compliance
- [ ] Single Responsibility
- [ ] Open/Closed
- [ ] Liskov Substitution
- [ ] Interface Segregation
- [ ] Dependency Inversion

### Coupling Analysis
- **High coupling detected**: [Locations]
- **Recommendation**: [How to decouple]
```

### For Security Reviewer
```markdown
### Secret Exposure
- [ ] No secrets hardcoded
- [ ] Environment variables used correctly
- [ ] No credentials in logs

### Authentication & Authorization
- [ ] Auth required where needed
- [ ] Permissions correctly scoped

### Injection Vectors
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Command injection prevention
```

### For Performance Reviewer
```markdown
### Bottlenecks Identified
- **Location**: [File:Line]
- **Issue**: [Description]
- **Impact**: [High/Med/Low]

### Scaling Concerns
- [ ] [Concern 1]
- [ ] [Concern 2]
```

---

## Links

- Context: `.agent/CONTEXT.md`
- Playbook: `.agent/PLAYBOOK.md`
- Vibe Coding: `.agent/VIBE_CODING.md`
- Critique Prompts: `.agent/VIBE_CRITIQUE_PROMPTS.md`
- Lessons: `.agent/tasks/lessons.md`

---

**Review thoroughly. Be specific. Recommend action.**
