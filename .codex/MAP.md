# Project Map

> **Purpose**: Visual project structure for quick orientation of the Edgebook repository.

---

## Root Level

```
edgebook/
├── AGENTS.md                   # AI guidance redirect (read .agent/AGENTS.md)
├── CLAUDE.md                   # Redirect for Claude Code
├── GEMINI.md                   # Redirect for Gemini CLI
├── README.md                   # Project overview
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guide
├── LICENSE                     # MIT license
├── pyproject.toml              # Dependencies and tooling
├── uv.lock                     # Locked dependency versions
├── mkdocs.yml                  # Documentation config
├── alembic.ini                 # Migration config
├── Makefile                    # Common commands
├── Dockerfile                  # Container image
└── .pre-commit-config.yaml     # Pre-commit hooks
```

---

## AI Agent Structure

```
.agent/                         # Active session management
├── CONTEXT.md                  # Entry point (project snapshot)
├── AGENTS.md                   # Agent operating manual
├── PRINCIPLES.md               # Operating principles
├── tasks/                      # Lessons and tasks
├── reviews/                    # Review templates
├── skills/                     # Reusable task workflows
│   ├── CATALOG.md              # Skills index
│   ├── start-session/
│   └── end-session/
└── workflows/                  # Automation references (health-check, test-ci, ...)

.codex/                         # Read-only context cache
├── README.md
├── MAP.md                      # This file
└── QUICKSTART.md               # Essential commands
```

---

## Source Code

```
src/edgebook/
├── __init__.py
├── main.py                     # FastAPI app entry point
├── core/
│   ├── config.py               # Pydantic settings
│   └── database.py             # SQLAlchemy session setup
├── api/
│   ├── accounts.py             # Fictional account & ledger transactions
│   └── cfb.py                  # CFB team/game/market/quote intake
├── cfb/                        # College football domain (isolated from ledger)
│   ├── models.py               # Team, Game, Market, MarketQuote
│   └── services.py             # CFB intake operations
├── ledger/                     # Double-entry ledger accounting
│   ├── models.py               # Accounts, postings
│   └── services.py             # Ledger business operations
└── utils/
    └── logging.py              # Edgebook logging utility
```

---

## Migrations & Tests

```
alembic/                        # Database migrations
└── versions/

tests/                          # Test suite
├── conftest.py
├── test_config.py
├── test_database.py
├── test_migrations.py
├── api/                        # API endpoint tests
├── ledger/                     # Ledger service tests
└── utils/                      # Utility tests
```

---

## Documentation

```
docs/
├── index.md                    # Documentation hub
├── project_charter.md          # Vision, scope, users, decision log
├── project_brief.md            # Objectives, metrics, timeline
├── implementation_schedule.md  # Phase roadmap
├── runbook.md                  # Operations guide
├── security.md                 # Responsible-use policy
├── getting_started.md          # Onboarding guide
├── development_standards.md    # Coding standards
├── checklists.md               # Quality gates
├── knowledge_base.md           # Patterns and gotchas
├── troubleshooting.md
├── ai_guide.md
├── ai_session_templates.md
├── architecture/
│   ├── system_overview.md
│   ├── data_modeling.md
│   └── adr/                    # Architecture decision records
├── api/
│   ├── README.md
│   └── openapi.yaml
└── data/
    ├── contracts.md
    └── dictionary.md
```

---

## Session Logs

```
session_logs/
├── README.md                   # Logging guidelines
├── TEMPLATE.md                 # Session log template
└── MM-DD-YYYY/                 # Daily session logs
    └── N - Title.md
```

---

## Key Paths for Common Tasks

### Starting a Session
1. `AGENTS.md` → `.agent/AGENTS.md` - Read first
2. `.agent/CONTEXT.md` - Current state
3. `.agent/skills/start-session/SKILL.md` - Session workflow
4. `session_logs/` - Review recent logs

### During Development
- `src/edgebook/` - Source code
- `tests/` - Test suite
- `docs/implementation_schedule.md` - Current priorities
- `.agent/skills/CATALOG.md` - Available workflows

### Closing a Session
1. `.agent/skills/end-session/SKILL.md` - Closing workflow
2. `session_logs/MM-DD-YYYY/N - Title.md` - Create log
3. `.agent/workflows/health-check.md` - Run checks
4. `docs/implementation_schedule.md` - Update if tasks completed

---

**Update Frequency**: When major structural changes occur.
