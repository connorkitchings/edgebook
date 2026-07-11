"""Create initial generic ledger and manual CFB intake schema.

Revision ID: 20260710_01
Revises:
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260710_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_immutable_ledger_triggers() -> None:
    """Prevent updates and deletes of posted journal entries and transactions."""
    dialect = op.get_bind().dialect.name
    tables = ("ledger_journal_entries", "ledger_transactions")
    if dialect == "sqlite":
        for table in tables:
            op.execute(
                f"""
                CREATE TRIGGER trg_{table}_immutable_update
                BEFORE UPDATE ON {table}
                BEGIN
                    SELECT RAISE(ABORT, '{table} is immutable');
                END;
                """
            )
            op.execute(
                f"""
                CREATE TRIGGER trg_{table}_immutable_delete
                BEFORE DELETE ON {table}
                BEGIN
                    SELECT RAISE(ABORT, '{table} is immutable');
                END;
                """
            )
    elif dialect == "postgresql":
        op.execute(
            """
            CREATE FUNCTION edgebook_prevent_ledger_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'Ledger journal entries and transactions are immutable';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        for table in tables:
            op.execute(
                f"""
                CREATE TRIGGER trg_{table}_immutable
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION edgebook_prevent_ledger_mutation();
                """
            )


def _drop_immutable_ledger_triggers() -> None:
    """Drop the dialect-specific append-only ledger guards before table removal."""
    dialect = op.get_bind().dialect.name
    tables = ("ledger_transactions", "ledger_journal_entries")
    if dialect == "sqlite":
        for table in tables:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable_update")
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable_delete")
    elif dialect == "postgresql":
        for table in tables:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table}")
        op.execute("DROP FUNCTION IF EXISTS edgebook_prevent_ledger_mutation()")


def upgrade() -> None:
    """Create generic ledger and isolated CFB domain tables."""
    op.create_table(
        "ledger_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_name", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("starting_bankroll_cents", sa.Integer(), nullable=False),
        sa.Column("current_balance_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "starting_bankroll_cents >= 0", name="ck_account_starting_nonnegative"
        ),
        sa.CheckConstraint("kind IN ('USER_ASSET', 'EQUITY')", name="ck_account_kind"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ledger_journal_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ledger_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("journal_entry_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_cents != 0", name="ck_transaction_amount_nonzero"),
        sa.CheckConstraint(
            "transaction_type IN ('DEPOSIT', 'WITHDRAWAL', 'WAGER_STAKE', "
            "'WAGER_PAYOUT', 'ADJUSTMENT')",
            name="ck_transaction_type",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["ledger_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["journal_entry_id"], ["ledger_journal_entries.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ledger_transactions_account_id", "ledger_transactions", ["account_id"]
    )
    op.create_index(
        "ix_ledger_transactions_journal_entry_id",
        "ledger_transactions",
        ["journal_entry_id"],
    )

    op.create_table(
        "cfb_teams",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_table(
        "cfb_games",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("home_team_id", sa.String(length=36), nullable=False),
        sa.Column("away_team_id", sa.String(length=36), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "home_team_id <> away_team_id", name="ck_game_distinct_teams"
        ),
        sa.CheckConstraint("status IN ('SCHEDULED')", name="ck_game_status"),
        sa.ForeignKeyConstraint(["away_team_id"], ["cfb_teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["cfb_teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cfb_games_away_team_id", "cfb_games", ["away_team_id"])
    op.create_index("ix_cfb_games_home_team_id", "cfb_games", ["home_team_id"])
    op.create_table(
        "cfb_markets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=False),
        sa.Column("market_type", sa.String(length=32), nullable=False),
        sa.Column("line_millipoints", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "market_type IN ('SPREAD', 'MONEYLINE', 'TOTAL')", name="ck_market_type"
        ),
        sa.CheckConstraint("status IN ('DRAFT', 'OPEN')", name="ck_market_status"),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "market_type", name="uq_market_game_type"),
    )
    op.create_index("ix_cfb_markets_game_id", "cfb_markets", ["game_id"])
    op.create_table(
        "cfb_market_quotes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("market_id", sa.String(length=36), nullable=False),
        sa.Column("selection", sa.String(length=32), nullable=False),
        sa.Column("american_odds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "selection IN ('HOME', 'AWAY', 'OVER', 'UNDER')", name="ck_quote_selection"
        ),
        sa.ForeignKeyConstraint(["market_id"], ["cfb_markets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("market_id", "selection", name="uq_quote_market_selection"),
    )
    op.create_index(
        "ix_cfb_market_quotes_market_id", "cfb_market_quotes", ["market_id"]
    )

    _create_immutable_ledger_triggers()


def downgrade() -> None:
    """Drop the initial CFB and generic ledger schema."""
    _drop_immutable_ledger_triggers()
    op.drop_index("ix_cfb_market_quotes_market_id", table_name="cfb_market_quotes")
    op.drop_table("cfb_market_quotes")
    op.drop_index("ix_cfb_markets_game_id", table_name="cfb_markets")
    op.drop_table("cfb_markets")
    op.drop_index("ix_cfb_games_home_team_id", table_name="cfb_games")
    op.drop_index("ix_cfb_games_away_team_id", table_name="cfb_games")
    op.drop_table("cfb_games")
    op.drop_table("cfb_teams")
    op.drop_index(
        "ix_ledger_transactions_journal_entry_id", table_name="ledger_transactions"
    )
    op.drop_index("ix_ledger_transactions_account_id", table_name="ledger_transactions")
    op.drop_table("ledger_transactions")
    op.drop_table("ledger_journal_entries")
    op.drop_table("ledger_accounts")
