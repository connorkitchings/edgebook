---
name: skill-template
description: "Template for creating new skills. Copy this file and fill in the sections."
metadata:
  trigger-keywords: "template, new skill, create skill"
  trigger-patterns: "^new skill, ^create skill"
---

# Skill Name

Brief description of what this skill accomplishes.

---

## When to Use

Describe the situations where this skill applies:
- When you need to X
- When Y happens
- Before Z milestone

**Do NOT use when:**
- Alternative approach is better
- Preconditions are not met

---

## Inputs

### Required
- Input 1: Description
- Input 2: Description

### Optional
- Input 3: Description (default: value)

---

## Steps

### Step 1: [Action Name]

**What to do:**
Detailed description of the action.

**Commands:**
```bash
# Example commands
command1
command2
```

**Validation:**
- [ ] Check 1
- [ ] Check 2

### Step 2: [Action Name]

**What to do:**
Detailed description.

**Code Example:**
```python
# Example code pattern
def example():
    pass
```

**Validation:**
- [ ] Check 1
- [ ] Check 2

### Step 3: [Action Name]

Continue pattern...

---

## Validation

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Verification Commands
```bash
# Run these to verify success
command1
command2
```

---

## Rollback

If you need to undo changes:

### Option 1: Undo Last Action
```bash
# Commands to undo
command1
```

### Option 2: Full Rollback
```bash
# Commands for full rollback
command1
command2
```

---

## Common Mistakes

1. **Mistake 1**: Description and how to avoid
2. **Mistake 2**: Description and how to avoid
3. **Mistake 3**: Description and how to avoid

---

## Related Skills

- **Related Skill 1**: When to use instead/complement
- **Related Skill 2**: When to use instead/complement

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **Related Doc**: `docs/path/to/doc.md`
- **Implementation Schedule**: `docs/implementation_schedule.md`

---

## Examples

### Example 1: Basic Usage

**Scenario:** Brief scenario description

**Steps:**
1. Step 1
2. Step 2
3. Step 3

**Result:** Expected outcome

### Example 2: Complex Usage

**Scenario:** Brief scenario description

**Steps:**
1. Step 1
2. Step 2 with special consideration
3. Step 3

**Result:** Expected outcome

---

**Remember: Update this skill when patterns change. Skills are living documents.**
