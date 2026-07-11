---
name: database-migrations
description: "Create and apply database schema modifications using Alembic."
metadata:
  trigger-keywords: "migration, schema, database update, alembic"
  trigger-patterns: "^migration, ^alembic"
---

# Database Migrations Skill

Use this skill whenever you need to modify database tables, columns, or constraints.

---

## 🏃 Migration Workflow

### 1. Define Models
* Modify or add models inside the relevant domain module (e.g. `cfb/models.py` or `ledger/models.py`).
* Ensure any new models are imported inside `alembic/env.py` so they are picked up during autogeneration.

### 2. Autogenerate Revision
Create the migration script using alembic:
```bash
uv run alembic revision --autogenerate -m "description"
```

### 3. Review the Script
* Inspect the generated file under `alembic/versions/`.
* Verify that table column typings, indexes, foreign keys, and unique constraints are defined correctly.

### 4. Run Upgrades & Verify
```bash
uv run alembic upgrade head
```
Verify that the test suite still runs successfully.
