# Vibe Coding with AI: Best Practices

> Human-AI collaboration principles for effective vibe coding. Source: [Vibe Coding Best Practices](https://towardsdatascience.com/vibe-coding-with-ai-best-practices-for-human-ai-collaboration-in-software-development/)

---

## The Core Loop

```
Human: Prompt → AI: Generate → Human + AI: Review → Human: Feedback → AI: Iterate
```

**The human remains the final arbiter.** AI has visibility into requirements, architecture, code, and tests—but only humans can assess broader context: business priorities, cost/latency constraints, reliability, maintainability, and explainability.

---

## Key Principles

### 1. Start with Test Queries

Before generating architecture or code, establish **representative test queries** that users are likely to ask.

- Test queries bound the scope for the AI
- Reduce risk of unnecessary complexity
- Provide concrete validation targets

**Example:** Instead of `"Build a search system"`, specify:
- `"How do articles discuss oil prices in 2015?"`
- `"What sport has the most coverage?"`
- `"Show business highlights from 2016"`

### 2. Architecture First, Code Second

**Always ask to create an architecture document first** before any code generation.

- Use a large thinking model (e.g., Gemini-3-Pro in Planning mode) for architecture
- Even if you have a design in mind, start fresh—then challenge and refine
- Developer role becomes **critical evaluation**: *"What if we simplified this?"*, *"What happens at 10X scale?"*

### 3. Validate the Design

Spend time reading architectural explanations and rationale.

- Understand tradeoffs between functionality, complexity, and maintainability
- This is still the developer's/architect's responsibility
- Ask: *"Is this the right balance?"*

### 4. Strengthen Through Edge Cases

Once architecture is understood, identify **edge test cases** that might break the design.

- Ask: *"How would the system handle 10X data?"*
- Ask: *"What if the user asks for X?"*
- Iterate on architecture until edge cases are addressed

### 5. Have AI Challenge Itself

Ask the AI to identify queries that **break its own architecture**.

- Request a different model (e.g., Claude Opus) for this critique
- Evaluate each suggestion with skeptical judgment
- Often, simpler modifications suffice—none of the complex changes are needed

**Example challenges:**
- Cross-document comparisons
- Exact phrase/keyword matching
- Temporal reasoning queries
- Contradiction detection

### 6. Detect and Challenge Over-Engineering

**Not every AI suggestion is necessary.**

- Question: *"Is this additional complexity warranted?"*
- Question: *"Will users actually need this feature?"*
- Push back on unnecessary components
- Simplicity is a strategic choice, not a limitation

### 7. Human Validates Before Implementation

**Explicit human checkpoint before code generation.**

- Review final architecture and edge case handling
- Confirm alignment with requirements and test queries
- Only then proceed to implementation

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Prevention |
|--------------|---------|------------|
| Garbage in, garbage out | Ambiguous prompts → wrong output | Define test queries upfront |
| No guardrails | AI unbounded → unexpected results | Set scope with requirements |
| Over-engineering | Complex architecture for simple problems | Challenge every addition |
| Skip validation | Trust AI blindly | Human reviews at every phase |
| No edge cases | System breaks in production | Test stress scenarios |

---

## Quick Reference Checklist

Before starting any task:

- [ ] Defined representative test queries
- [ ] Produced architecture document
- [ ] Validated design rationale
- [ ] Identified and addressed edge cases
- [ ] Challenged over-engineering tendencies
- [ ] Confirmed human validation checkpoint passed

During implementation:

- [ ] Follow Prompt → Generate → Review → Feedback → Iterate loop
- [ ] Review AI execution logs
- [ ] Understand the code, even if AI generated it
- [ ] Maintain human-in-the-loop at every phase

---

## Key Takeaways

1. **AI accelerates, humans validate** — Speed does not replace judgment
2. **Test queries bound scope** — Define examples before coding
3. **Architecture before code** — Always design first
4. **Challenge complexity** — Not every suggestion is necessary
5. **Iterate through review** — Human-in-the-loop at every phase
6. **Human remains final arbiter** — Only humans weigh trade-offs and decide fitness for production

---

## Specialized Review Agents

The repo includes 10 specialized review agents to provide focused expertise on specific aspects of your project.

### Agent Priorities

| Priority | Agent | When to Use |
|----------|-------|-------------|
| 1 | **Planning Orchestrator** | Start of any new feature or project |
| 2 | **Architecture Reviewer** | After planning, before implementation |
| 3 | **Security Reviewer** | Before commits with security impact |
| 4 | **Over-Engineering Detector** | When code feels too complex |
| 5 | **Edge Case Challenger** | After architecture design |
| 6 | **Data Quality Reviewer** | Data-related changes |
| 7 | **Testing Reviewer** | Before PRs |
| 8 | **Performance Reviewer** | Before release |
| 9 | **Modularity Reviewer** | Code organization concerns |
| 10 | **Abstraction Reviewer** | Interface design changes |

### How to Use

1. Select the agent from `.agent/VIBE_CRITIQUE_PROMPTS.md`
2. Fill in your context
3. Submit to AI
4. Save output to `.agent/reviews/`

### Quick Invocation Examples

```
# Planning
@agent Plan a new user dashboard feature

# Security check
@agent Review src/api/auth.py for security issues

# Architecture
@agent Review the proposed RAG architecture
```

### Review Flow Example

```
Task → Planning Orchestrator → Architecture Reviewer 
     → Edge Case Challenger → Over-Engineering Detector 
     → Implementation → Testing Reviewer → Security Reviewer
```

---

## Links

- Principles: `.agent/PRINCIPLES.md`
- Playbook: `.agent/PLAYBOOK.md`
- Lessons: `.agent/tasks/lessons.md`
- Start session: `.agent/skills/start-session/SKILL.md`
- Critique Prompts: `.agent/VIBE_CRITIQUE_PROMPTS.md`
- Review Template: `.agent/reviews/TEMPLATE.md`

---

**AI is a tool, not a replacement. Use it wisely.**
