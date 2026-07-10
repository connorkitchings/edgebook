# AI Development Session Templates

This document provides **copy-paste templates** for starting and ending an AI-assisted development
session inside the Vibe Coding System.  Each template ensures the assistant gathers the right
context, operates within project standards, and records its work correctly.

---

## 🟢 Session Start Template

```markdown
### Session Start

1. **Load Core Context**
   - Open and skim `README.md` for high-level purpose.
   - Review `docs/project_charter.md` for goals & stakeholders.
     *(link in log as `[PRD-feat:X]` where appropriate)*
   - Check the latest session log (`session_logs/`) to understand recent activity.
     Use syntax `[LOG:YYYY-MM-DD]` when referencing it.
   - Read any task-specific docs (e.g., `docs/implementation_schedule.md`).

2. **Identify the User Request**
   - Summarize the user’s objective in 1–2 sentences (write this in the log).
   - Clarify ambiguities with questions before coding.

3. **Update the Plan**
   - Call `update_plan` to reflect new tasks or changes.

4. **Declare Next Steps**
   - Briefly outline the immediate actions (research, code edits, etc.).

> *You are now ready to begin executing steps.*
```

---

## 🔴 Session End Template

```markdown
### Session End

1. **Summarize Work Performed**
   - Bullet the major actions (files created/edited, commands run).
   - State whether acceptance criteria were met.

2. **Update Documentation**
   - If a new decision was made, add an entry to `prd.md` under **DECISION LOG**.
   - If new knowledge was discovered, add or update `docs/knowledge_base.md`.

3. **Create/Append Session Log**
   - Write `session_logs/YYYY-MM-DD.md` with:
     * Context-links (`[PRD-feat:X]`, `[LOG:...]`).
     * Actions taken.
     * Next-step recommendations.

4. **Commit & Push**
   - Stage relevant files.
   - Use a descriptive commit message (e.g., `feat: implement data ingestion flow [PRD-feat:B]`).

5. **Close the Plan**
   - Call `update_plan` marking completed items.

> *Session closed. Awaiting next user input.*
```

---

### Usage Tips

- **Automate**: You can store these snippets in your editor snippets for one-click insertion.
- **Enforce Links**: Always use the linking syntax to keep logs and docs interconnected.
- **Be Concise**: Logs should capture *decisions and results*, not every keystroke.
- **Review Checklist**: Before ending, run `pre-commit run --all-files` to catch linting issues.

---

By following these templates, each AI development session starts with the right context and ends
with a clean, traceable record—ensuring continuity and accountability across the project.
