# AI-Friendly Documentation Guide for Engineering & Agentic Projects

Goal: Organize docs so humans and AI agents can navigate your codebase, discover workflows, and make safe changes without reading your entire wiki.

---

## 1. Core Principles

1. Minimize required context: design the repo so the “next step” is obvious from where the agent already is (file, CLI, test output).
1. Treat every output as a prompt: logs, errors, test results, and CLI responses should suggest concrete next actions.
1. Make code self-documenting by keeping canonical, short docs as close as possible to where work happens (comments, `--help`, docstrings).
1. Organize by workflow or feature, not just abstract layers.
1. Make docs testable via a realistic “prompt → PR” victory test.

---

## 2. Documentation Layers

Think in layers from closest to the code up to deep design docs.

### 2.1 Layer 0 — Inline & Self-Documenting

These are the first things an AI agent sees; they must be accurate and concise.

- **Code comments and module headers**
  - At the top of critical files, briefly describe:
    - What this file or module does
    - Key assumptions
    - Typical usage patterns
- **Docstrings**
  - For public functions and classes, document:
    - Arguments, types, and defaults
    - Return values
    - Failure modes and side effects
    - Simple usage examples
- **CLI / tool `--help`**
  - Every command exposes a rich `--help` with:
    - One-line description
    - Required and optional arguments
    - Common examples
    - Exit codes or error semantics

Rule of thumb: if an agent must leave the current context to understand what to do next, Layer 0 is under-documented.

### 2.2 Layer 1 — Front-Door AI Doc (`AI_GUIDE.md`)

A single, short “front door” doc at the repo root that orients both humans and agents.

**Location:** `./AI_GUIDE.md`  
**Target length:** roughly 3–5 pages.

Recommended structure:

1. Purpose & scope  
   1. What this repo does in one short paragraph.  
   1. Primary domains (for example: setlist prediction, fraud detection, internal tools).
1. How to work in this repo  
   1. Short playbook for common tasks:
      - “To add a feature: run X, edit Y, run tests Z.”
      - “To debug a failure: start with A, then B.”
   1. Links to more detailed workflow docs.
1. Repo map  
   1. High-level directory overview:
      - `/features/...` – feature-oriented code
      - `/configs/...` – configuration and pipelines
      - `/docs/...` – deeper docs
1. Key tools and interfaces  
   1. CLIs: names, one-line descriptions, and a “start here” command.  
   1. Tool endpoints (MCP or similar): what they do conceptually.
1. Safety, guardrails, and non-goals  
   1. Data privacy rules  
   1. Things that must not be changed without human review  
   1. Known fragile or legacy areas
1. Victory test (prompt → PR)  
   1. One or two concrete “victory scenarios,” for example:
      - “Add a new feature flag to the search endpoint.”
   1. High-level steps:
      - Run this CLI to scaffold or validate
      - Edit these files
      - Run this test or E2E flow

### 2.3 Layer 2 — Workflow Docs (Task-Centric)

Workflow docs describe how to do recurring tasks, not abstract concepts.

**Location:** `./docs/workflows/`

Suggested files:

- `feature_development.md`
- `bugfix_troubleshooting.md`
- `data_pipeline_changes.md`
- `model_training_and_eval.md`
- `deployment_and_rollbacks.md`

Each workflow doc should follow a template:

1. When to use this  
   1. Short list of scenarios.
1. Inputs  
   1. Required permissions, tools, config files, and env vars.
1. Step-by-step procedure  
   1. Numbered steps with copy-pastable commands.  
   1. Expected outputs and common errors.  
   1. For each error, give the next command or doc to consult.
1. Validation  
   1. How to know you are done:
      - Tests to run
      - Metrics or dashboards to check
1. Rollback / escape hatch  
   1. How to revert if something goes wrong.

These workflows should line up with your repo structure. If you organize by feature, the workflow docs should point directly to those feature folders.

### 2.4 Layer 3 — Deep Design & Architecture

Deep reference docs, not starting points.

**Location:** `./docs/architecture/`

Contents:

- System overview diagrams
- Data model and schema docs
- ADRs (architecture decision records)
- Modeling notes and experiment reports

Each file should start with:

- Status: `active`, `deprecated`, or `experimental`
- Last validated date
- TL;DR with three to five bullets
- “Who should read this and when”

Agents and humans should only dive here when doing major refactors or core design work.

---

## 3. Outputs and Tools as Documentation

### 3.1 Outputs as Next-Step Prompts

For CLIs, scripts, and services, design outputs as mini-docs for the next step.

On success:

- Print a short confirmation.
- Suggest at least one sensible next action with an exact command.

On failure:

- Say what went wrong in plain language.
- Show how to fix it (for example, the correct command, flag, or config).
- Link to a relevant workflow or runbook if needed.

### 3.2 CLI and Tool-Catalog Docs

If you expose tools via CLI and a tool-calling protocol (such as MCP):

- **CLI docs**
  - Rich `--help` with examples.
  - A small `README` in `./tools/<tool_name>/` that mirrors the CLI usage.
- **Tool catalog docs**
  - Short schema or capability overview in `./docs/tools/`:
    - What the tool does
    - Inputs and outputs
    - Typical call patterns
    - Any limits or safety notes

---

## 4. Suggested Directory Layout

Here is a sample repo layout optimized for AI and human navigation:

```text
.
├─ README.md
├─ AI_GUIDE.md               # front-door doc for agents and humans
├─ docs/
│  ├─ workflows/
│  │  ├─ feature_development.md
│  │  ├─ bugfix_troubleshooting.md
│  │  ├─ data_pipeline_changes.md
│  │  ├─ model_training_and_eval.md
│  │  └─ deployment_and_rollbacks.md
│  ├─ architecture/
│  │  ├─ system_overview.md
│  │  ├─ data_modeling.md
│  │  └─ adr/
│  │     ├─ adr-0001-initial-architecture.md
│  │     └─ ...
│  ├─ tools/
│  │  ├─ my_cli_tool.md
│  │  └─ my_mcp_tool.md
│  └─ glossary.md
├─ features/
│  ├─ search/
│  │  ├─ api.py
│  │  ├─ service.py
│  │  ├─ model.py
│  │  └─ tests/
│  └─ ...
└─ tools/
   └─ cli/...
