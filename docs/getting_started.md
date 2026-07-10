# Getting Started

> **Purpose:** This document is the *first stop* after cloning the template. It guides you (or an AI
> co-pilot) to turn this generic template into a focused, real project.
>
> **How to use:** Work through the "Project Initialization" checklist below.  When a prompt says
> *AI-ACTION*, feed the indented question to your AI assistant and paste the answer back here (or
> link to the relevant doc).  Repeat until all placeholders are filled.

---

## ⚡ Quick Start (5 Minutes)

Get your project running in minutes with the interactive setup script:

```bash
# 1. Run interactive setup
python scripts/setup_project.py

# 2. Install dependencies
make install
# OR: uv sync

# 3. Verify everything works
make validate

# 4. Run tests
make test

# 5. Start development
make dev
```

**What the setup script does:**
- Prompts for project details (name, type, author)
- Updates all template files automatically
- Creates a feature branch for initial work
- Sets up `.gitignore` with standard patterns

**Next steps after setup:**
1. Review changes: `git diff`
2. Customize `.agent/CONTEXT.md` with your project specifics
3. Start your first session: Read `.agent/skills/start-session/SKILL.md`

---

## 🔰 Project Initialization (AI-Assisted)

| Section             | Prompt (AI-ACTION)                                                                                   |
|---------------------|------------------------------------------------------------------------------------------------------|
| Project Overview    | "Summarize in 2–3 sentences: What problem does this project solve and why does it matter?"             |
| Success Criteria    | "List measurable KPIs or qualitative goals that indicate project success."                               |
| Stakeholders        | "Name primary stakeholders & their roles (e.g., Product Manager, Data Scientist, Domain Expert)."      |
| Data Sources        | "Describe each data source: origin, owner, refresh cadence, and access method."                        |
| Technical Stack     | "Recommend languages, frameworks, cloud services and justify each choice briefly."                   |
| High-Level Timeline | "Propose major milestones with rough dates or sprint numbers."                                       |
| Risks & Mitigations | "List top 3 project risks and suggested mitigations."                                                |
| Governance          | "Outline how decisions will be recorded (e.g., DECISION LOG), and who has merge approval rights."      |

*After each answer is captured, consider linking to deeper docs such as `project_charter.md`,
 `implementation_schedule.md`, or creating new files under `docs/`.*

---

## 🧹 Template Cleanup Checklist

Once the above blanks are filled and the project scope is clear, delete or keep the following assets
as appropriate:

- **`docs/*`**
  - `checklists.md` – Keep if your team will follow the default checklists, otherwise remove or
    merge into another doc.
  - `development_standards.md` – Keep unless your org has a conflicting standard.
  - `knowledge_base.md` – Delete if you don’t plan to maintain an internal KB.
- **`notebooks/`** – Remove if the project will *not* use exploratory notebooks (e.g.,
  production-only pipeline).
- **`flows/` & `prefect.yaml`** – Delete if you won’t orchestrate with Prefect.
- **`models/` & `reports/`** – Delete until the project produces artifacts.
- **CI/CD Workflows in `.github/`** – Cull any workflows you won’t need (e.g., Docker publish) to
  reduce pipeline noise.
- **Docs Sections** – Update `mkdocs.yml` nav to remove deleted pages.

> **Tip:** Perform cleanup in a dedicated pull request so the diff clearly shows removed items.

---

## 🚀 Starting a New Project

This template is designed for new projects. Here's how to use it for the first time:

### Step 1: Get the Template

```bash
# Clone the template
git clone https://github.com/your-username/vibe-coding-template.git
cd vibe-coding-template

# Or use as GitHub template (creates new repo)
# Click "Use this template" on GitHub
```

### Step 2: Run Setup Script

```bash
# Interactive setup - prompts for project details
python scripts/setup_project.py
```

The setup will ask for:
- Project name
- Project type (data-pipeline, web-app, cli-tool, ml-model)
- Short description
- Author name
- Git initialization options

### Step 3: Customize for Your Needs

After setup completes:

1. **Review the changes:**
   ```bash
   git status
   git diff
   ```

2. **Update project-specific docs:**
   - `.agent/CONTEXT.md` - Project snapshot and current status
   - `docs/implementation_schedule.md` - Your project timeline
   - `docs/project_charter.md` - Project vision and goals

3. **Adjust development standards if needed:**
   - `docs/development_standards.md` - Code quality standards
   - `docs/checklists.md` - Quality gates

### Step 4: Start Development

```bash
# Create a feature branch for your first task
git checkout -b feat/your-first-task

# Read the session start workflow
cat .agent/skills/start-session/SKILL.md

# Follow the skill to begin your first development session
```

---

This guide provides instructions for setting up your local development environment to work with the
Vibe Coding Data Science Template.

## Prerequisites

- **Python 3.10+**: Ensure you have a compatible Python version installed.
- **Git**: For version control.
- **`uv`**: The project's package manager. If you don't have it, install it with `pip install uv`.

## 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone <repository-url>
cd <repository-name>
```

## 2. Set Up the Virtual Environment

This project uses `uv` for package and environment management. Create and activate a virtual environment:

```bash
# Create a virtual environment named .venv
uv venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

## 3. Install Dependencies

Install all required project dependencies using `uv`:

```bash
uv pip install -r requirements.txt
```

## 4. Set Up Pre-Commit Hooks

Install the pre-commit hooks to ensure your contributions adhere to the project's quality standards:

```bash
pre-commit install
```

## 5. Run the Tests

Verify that the setup is correct by running the test suite:

```bash
uv run pytest
```

## 6. View the Documentation

To serve the documentation site locally, run the following command:

```bash
mkdocs serve
```

Then, open your browser to `http://127.0.0.1:8000` to view the documentation.

You are now ready to start developing!
