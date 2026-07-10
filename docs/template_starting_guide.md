# From Template to Project Kickoff Guide

> This repository currently ships as the **Vibe Coding Data Science Template**.  
> Use this guide the moment you convert it into a named, live project.

The checklist below captures the questions you must answer and the specific documentation/code
artifacts you need to touch before shipping the first “real” commit.

---

## 1. Define the Project Charter (Answer These Questions)

- What is the official project name and elevator pitch?
- Who are the sponsoring stakeholders and end users?
- Which business outcomes or metrics define success?
- What is in scope vs. explicitly out of scope for the first release?
- What timelines or milestones are already committed?

**Update**
- `docs/project_brief.md` — Fill every section with project-specific context.
- `docs/project_charter.md` — Replace template placeholders (vision, personas, stories, features, risks).
- `docs/project_brief.md` / `docs/project_charter.md` decision log — capture any trade-offs made during kickoff.

---

## 2. Align Governance & Schedule

- Which task from `docs/implementation_schedule.md` represents your first deliverable?
- Who owns each track (Docs, DataOps, DevEx, etc.) for the upcoming weeks?
- Are there escalation triggers already in play (schemas, security, external dependencies)?

**Update**
- `docs/implementation_schedule.md` — Swap placeholder owners with real people, set realistic statuses/dates.
- `session_logs/` — Start a dated session log documenting kickoff decisions and links to schedule rows.
- `AGENTS.md` / `AI_GUIDE.md` (if needed) — Tailor routing rules or playbooks unique to the project/org.

---

## 3. Establish Technical Foundations

Answer before coding:
- What environments (local, staging, prod) are required on day one?
- Which data sources or APIs will power the first feature?
- How will secrets/configuration be managed outside of the repo?

**Update / Implement**
- `src/vibe_coding/core/config.py` — Replace placeholder settings with real configuration entries and load paths.
- `docs/runbook.md` — Record environment setup, monitoring entry points, and escalation contacts.
- `docs/security.md` (if applicable) — Document initial secrets handling strategy or required approvals.

### (Optional) Node.js & Session Handoff Tools

If you want cross-tool session handoff with cli-continues:

- **Install Node.js 22+**: https://nodejs.org/ (or use nvm)
- **Optional install**: `npm install -g continues` (or use `npx continues`)
- **Documentation**: `docs/tools/cli-continues.md`
- **Workflow**: `.agent/workflows/session-handoff.md`

This is completely optional — the template works fully without Node.js. cli-continues enables seamless context transfer between Claude, Copilot, Gemini, Codex, OpenCode, Factory Droid, and Cursor.

---

## 4. Customize Data & Modeling Stubs

Questions to answer:
- What raw datasets or API endpoints do you ingest first?
- What feature transformations are mandatory for MVP?
- Which baseline model or rule set delivers immediate value?

**Implement**
- `src/vibe_coding/data/make_dataset.py` & `process_features.py` — Replace logging stubs with ingestion and feature logic.
- `docs/data/contracts.md` & `docs/data/dictionary.md` — Define schemas, freshness, quality expectations.
- `src/vibe_coding/models/train_model.py`, `predict_model.py`, `evaluate_model.py` — Implement baseline pipeline end to end.
- `docs/models/model_card.md` & `docs/models/experiment_plan.md` — Capture goals, metrics, evaluation plan early.
- `tests/` — Add regression tests for ingestion, feature engineering, and model behavior (update coverage goals).

---

## 5. Productize Interfaces & Tooling

- What is the primary user interaction (CLI, API, UI) for the first milestone?
- How will you demonstrate a happy-path run to stakeholders?
- Which automation or CI updates are needed beyond the template defaults?

**Update**
- `src/vibe_coding/api/` or CLI entrypoints — Implement concrete endpoints/commands backed by the new logic.
- `docs/workflows/` (feature, deployment, data pipeline) — Tailor playbooks to your operational reality.
- `.github/workflows/ci.yml` — Validate required jobs (add additional steps/tests as needed).
- `CHANGELOG.md` — Start capturing project-specific changes from the first customization commit.

---

## 6. Confirm Readiness Before Coding Sprints

All boxes should be checked before sprinting on features:
- [ ] Project brief & charter fully populated with current answers.
- [ ] Implementation schedule updated with owners, statuses, and immediate tasks.
- [ ] Kickoff session log committed and linked to the above artifacts.
- [ ] Configuration, data, and modeling plans documented with responsible owners.
- [ ] Testing, CI, and documentation updates identified for the first deliverable.

Once the checklist is green, proceed with the Victory Test from `AGENTS.md` to ensure the toolchain runs end-to-end under the new project identity, then start executing the tasks tracked in the schedule.
