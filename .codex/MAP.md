# Project Map

> **Purpose**: Visual project structure for quick orientation.

---

## Root Level

```
Vibe-Coding/
├── AGENTS.md                   # Multi-tool AI guidance (read first)
├── CLAUDE.md                   # Redirect to AGENTS.md
├── GEMINI.md                   # Redirect to AGENTS.md
├── README.md                   # Project overview
├── CHANGELOG.md                # Version history
├── pyproject.toml              # Dependencies and tooling
├── mkdocs.yml                  # Documentation config
├── prefect.yaml                # Workflow orchestration (optional)
└── .pre-commit-config.yaml     # Pre-commit hooks
```

---

## AI Agent Structure

```
.agent/                         # Active session management
├── CONTEXT.md                  # Entry point (project snapshot)
├── skills/                     # Reusable task workflows
│   ├── CATALOG.md              # Skills index
│   ├── start-session/
│   │   └── SKILL.md            # Session initialization
│   └── end-session/
│       └── SKILL.md            # Session closing
└── workflows/                  # Automation scripts
    └── health-check.md         # Pre-commit validation

.codex/                         # Read-only context cache
├── README.md                   # Purpose explanation
├── MAP.md                      # This file
└── QUICKSTART.md               # Essential commands
```

---

## Source Code

```
src/
└── vibe_coding/
    ├── __init__.py
    └── utils/
        └── agent_logging.py    # Logging utilities
```

---

## Tests

```
tests/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── test_endpoints.py
├── core/
│   ├── __init__.py
│   └── test_config.py
├── data/
│   ├── __init__.py
│   ├── test_make_dataset.py
│   └── test_process_features.py
└── models/
    ├── __init__.py
    ├── test_evaluate_model.py
    ├── test_predict_model.py
    └── test_train_model.py
```

---

## Documentation

```
docs/
├── index.md                    # Documentation hub
├── project_charter.md          # Project vision and goals
├── project_brief.md            # Executive summary
├── implementation_schedule.md  # Current priorities
├── development_standards.md    # Coding standards
├── checklists.md               # Quality gates
├── knowledge_base.md           # Solutions and patterns
├── runbook.md                  # Operations guide
├── security.md                 # Security guidelines
├── glossary.md                 # Project terminology
├── getting_started.md          # Onboarding guide
├── template_starting_guide.md  # Template adaptation
├── ai_guide.md                 # AI tool guidance (legacy)
├── ai_session_templates.md     # Session templates (legacy)
├── architecture/
│   ├── system_overview.md      # Architecture overview
│   ├── data_modeling.md        # Data architecture
│   ├── ai_docs_organization_guide.md
│   └── adr/                    # Architecture decisions
├── api/
│   ├── README.md
│   └── openapi.yaml            # API specification
├── data/
│   ├── contracts.md            # Data contracts
│   └── dictionary.md           # Data dictionary
├── models/
│   ├── model_card.md           # Model documentation
│   └── experiment_plan.md      # Experiment tracking
├── guides/
│   ├── silo_architecture.md    # Data silo pattern
│   └── web_architecture.md     # Web architecture
├── workflows/
│   ├── feature_development.md
│   ├── bugfix_troubleshooting.md
│   ├── data_pipeline_changes.md
│   ├── model_training_and_eval.md
│   └── deployment_and_rollbacks.md
├── tools/
│   ├── mcp_tooling.md          # MCP integration
│   ├── cli_tool_template.md    # CLI tool guide
│   └── cli_agent_coding_guide.md
└── archive/
    ├── v1.0.0_implementation_summary.md
    ├── v1.1.0_enhancements_summary.md
    ├── implementation_checklist.md
    └── enhancements_completed.md
```

---

## Scripts

```
scripts/
├── cli.py                      # CLI interface
├── init_session.py             # Session initialization
├── init_template.py            # Template setup
├── check_links.py              # Documentation link checker
└── test_notebooks.py           # Notebook testing
```

---

## Session Logs

```
session_logs/
├── README.md                   # Logging guidelines
├── TEMPLATE.md                 # Session log template
├── log_template.md             # Alternative template
└── YYYY-MM-DD/                 # Daily session logs
    ├── 01.md
    ├── 02.md
    └── ...
```

---

## Configuration

```
config/
├── github/                     # GitHub templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── feature_request.md
│       └── improvement.md
└── (other config files)
```

---

## Legacy Structure (To Be Removed)

```
.agents/                        # Old agent structure
├── AGENTS.md                   # Superseded by /AGENTS.md
├── prompts/
│   ├── navigator.md
│   ├── dataops.md
│   └── specialist.md
└── skills/
    ├── CATALOG.md
    ├── context-audit.py
    └── web_init.py
```

---

## Key Paths for Common Tasks

### Starting a Session
1. `AGENTS.md` - Read first
2. `.agent/CONTEXT.md` - Current state
3. `.agent/skills/start-session/SKILL.md` - Session workflow
4. `session_logs/` - Review last 3-5 logs

### During Development
- `src/` - Source code
- `tests/` - Test suite
- `docs/implementation_schedule.md` - Current priorities
- `.agent/skills/CATALOG.md` - Available workflows

### Closing a Session
1. `.agent/skills/end-session/SKILL.md` - Closing workflow
2. `session_logs/YYYY-MM-DD/NN.md` - Create log
3. `.agent/workflows/health-check.md` - Run checks
4. `docs/implementation_schedule.md` - Update if needed

### Documentation
- `docs/index.md` - Start here
- `mkdocs.yml` - Navigation structure
- Run: `mkdocs serve` for local preview

---

**Last Updated**: 2026-02-11
**Update Frequency**: When major structural changes occur
