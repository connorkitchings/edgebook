---
name: database-migration
description: "Create and apply database migrations safely using Alembic or similar tools."
metadata:
  trigger-keywords: "migration, database, schema, alembic, migrate"
  trigger-patterns: "^migration, ^schema change, ^database update"
---

# Database Migration Skill

Safely create and apply database schema changes with Alembic.

---

## When to Use

- Adding new tables or columns
- Modifying existing schema
- Creating indexes or constraints
- Data migrations (transform existing data)

**Do NOT use when:**
- Just adding data (use ingestion scripts)
- Emergency production fixes (use runbook instead)

---

## Inputs

### Required
- Change description: What are you adding/modifying?
- Current schema location: Path to models/ORM files
- Migration tool: Alembic, Django migrations, etc.

### Optional
- Database URL: If different from default (uses env var)
- Downgrade path: How to reverse the change

---

## Steps

### Step 1: Verify Current State

**What to do:**
Check current database state and ensure you're on a feature branch.

**Commands:**
```bash
# Check branch (CRITICAL - never on main)
git branch

# View current migration status
alembic current
alembic history

# Check for uncommitted changes
git status
```

**Validation:**
- [ ] On feature branch (`feat/` prefix)
- [ ] No uncommitted changes on main
- [ ] Database connection working

### Step 2: Create Migration

**What to do:**
Generate migration file with auto-detected changes.

**Commands:**
```bash
# Auto-generate migration
alembic revision --autogenerate -m "add users table"

# Or create empty migration for manual SQL
alembic revision -m "custom data migration"
```

**Code Pattern (if manual):**
```python
"""add users table

Revision ID: abc123
Revises: def456
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    # Create table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create index
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('ix_users_email')
    op.drop_table('users')
```

**Validation:**
- [ ] Migration file created in `alembic/versions/`
- [ ] Revision ID is unique
- [ ] Upgrade/downgrade functions defined
- [ ] Idempotent (can run multiple times safely)

### Step 3: Review Migration

**What to do:**
Manually review auto-generated migration before applying.

**Check for:**
- [ ] Correct column types
- [ ] Proper nullable constraints
- [ ] Indexes on foreign keys
- [ ] No unintended changes
- [ ] Downgrade is complete (not just pass)

**Common Issues:**
- Renamed columns detected as drop + add (fix manually)
- Missing indexes on FKs (add manually)
- Default values not set (add manually)

### Step 4: Test Migration

**What to do:**
Apply migration to local/test database and verify.

**Commands:**
```bash
# Apply migration
alembic upgrade head

# Verify in database
psql -d mydb -c "\dt"  # List tables
psql -d mydb -c "\d users"  # Describe table

# Test downgrade
alembic downgrade -1
alembic upgrade head  # Re-apply
```

**Validation:**
- [ ] Upgrade succeeds
- [ ] Schema looks correct
- [ ] Downgrade succeeds
- [ ] Can upgrade again after downgrade

### Step 5: Update Models

**What to do:**
Update ORM models to match new schema.

**Code Pattern:**
```python
# src/models/user.py
from sqlalchemy import Column, Integer, String, DateTime
from src.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
```

**Validation:**
- [ ] Model matches migration exactly
- [ ] Type hints correct
- [ ] Relationships defined (if applicable)

### Step 6: Add Tests

**What to do:**
Add tests for new schema.

**Test Pattern:**
```python
def test_users_table_exists(db_session):
    """Verify users table was created."""
    result = db_session.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
    )
    assert result.scalar() is True

def test_user_email_unique(db_session):
    """Verify email uniqueness constraint."""
    with pytest.raises(IntegrityError):
        user1 = User(email="test@example.com")
        user2 = User(email="test@example.com")
        db_session.add_all([user1, user2])
        db_session.commit()
```

---

## Validation

### Success Criteria
- [ ] Migration file created and reviewed
- [ ] Upgrade/downgrade tested locally
- [ ] ORM models updated
- [ ] Tests added and passing
- [ ] Documentation updated (if schema changes affect API)

### Verification Commands
```bash
# Run migration
cd backend && alembic upgrade head

# Run tests
uv run pytest tests/test_migrations.py -v

# Lint check
uv run ruff check src/models/
```

---

## Rollback

### If Migration Fails

```bash
# Check current state
alembic current

# Downgrade one step
alembic downgrade -1

# Or downgrade to specific revision
alembic downgrade abc123

# Fix issues and regenerate
alembic revision --autogenerate -m "fixed migration"
```

### If Already Applied to Production

**DON'T downgrade production!** Instead:
1. Create new migration to fix the issue
2. Test thoroughly in staging
3. Apply as normal migration

---

## Common Mistakes

1. **Forgetting nullable=False**: Always specify nullable constraint
2. **Missing downgrade**: Must provide downgrade path
3. **Not testing downgrade**: Always verify downgrade works
4. **Modifying existing migrations**: Never edit applied migrations
5. **Adding data in migration**: Use separate data migration script

---

## Related Skills

- **Data Ingestion**: For populating new tables with data
- **API Endpoint**: If adding API for new tables
- **Test Writer**: For writing migration tests

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **Database Schema**: `docs/architecture/database_schema.md`
- **Alembic Docs**: https://alembic.sqlalchemy.org/

---

## Examples

### Example 1: Add New Table

**Scenario:** Adding a users table with email and timestamps.

**Migration:**
```python
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade():
    op.drop_table('users')
```

### Example 2: Add Column to Existing Table

**Scenario:** Adding a `status` column to existing `orders` table.

**Migration:**
```python
def upgrade():
    op.add_column('orders', sa.Column('status', sa.String(50), nullable=True))
    # Backfill data if needed
    op.execute("UPDATE orders SET status = 'pending' WHERE status IS NULL")
    # Make non-nullable after backfill
    op.alter_column('orders', 'status', nullable=False)

def downgrade():
    op.drop_column('orders', 'status')
```

---

**Remember: Test migrations thoroughly before committing.**
