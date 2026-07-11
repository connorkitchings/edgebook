"""Add manual bet lifecycle and final game scores.

Revision ID: 20260711_02
Revises: 20260710_01
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260711_02"
down_revision: str | None = "20260710_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cfb_games") as batch_op:
        batch_op.add_column(sa.Column("home_score", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("away_score", sa.Integer(), nullable=True))
        batch_op.drop_constraint("ck_game_status", type_="check")
        batch_op.create_check_constraint(
            "ck_game_status", "status IN ('SCHEDULED', 'FINAL')"
        )
        batch_op.create_check_constraint(
            "ck_game_scores_nonnegative",
            "(home_score IS NULL OR home_score >= 0) AND "
            "(away_score IS NULL OR away_score >= 0)",
        )
        batch_op.create_check_constraint(
            "ck_game_final_scores_present",
            "(status = 'SCHEDULED' AND home_score IS NULL AND away_score IS NULL) OR "
            "(status = 'FINAL' AND home_score IS NOT NULL AND away_score IS NOT NULL)",
        )

    op.create_table(
        "wagering_bets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=False),
        sa.Column("market_id", sa.String(length=36), nullable=False),
        sa.Column("quote_id", sa.String(length=36), nullable=False),
        sa.Column("stake_transaction_id", sa.String(length=36), nullable=False),
        sa.Column("payout_transaction_id", sa.String(length=36), nullable=True),
        sa.Column("idempotency_key", sa.String(length=100), nullable=True),
        sa.Column("selection", sa.String(length=32), nullable=False),
        sa.Column("market_type", sa.String(length=32), nullable=False),
        sa.Column("line_millipoints", sa.Integer(), nullable=True),
        sa.Column("american_odds", sa.Integer(), nullable=False),
        sa.Column("stake_cents", sa.Integer(), nullable=False),
        sa.Column("bankroll_before_cents", sa.Integer(), nullable=False),
        sa.Column("payout_cents", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("stake_cents > 0", name="ck_bet_stake_positive"),
        sa.CheckConstraint(
            "bankroll_before_cents >= stake_cents", name="ck_bet_bankroll_covers_stake"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'WON', 'LOST', 'PUSH')", name="ck_bet_status"
        ),
        sa.CheckConstraint(
            "selection IN ('HOME', 'AWAY', 'OVER', 'UNDER')",
            name="ck_bet_selection",
        ),
        sa.CheckConstraint(
            "market_type IN ('SPREAD', 'MONEYLINE', 'TOTAL')",
            name="ck_bet_market_type",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["ledger_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["market_id"], ["cfb_markets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["quote_id"], ["cfb_market_quotes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["stake_transaction_id"], ["ledger_transactions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["payout_transaction_id"], ["ledger_transactions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stake_transaction_id"),
        sa.UniqueConstraint("payout_transaction_id"),
        sa.UniqueConstraint(
            "account_id", "idempotency_key", name="uq_bet_account_idempotency"
        ),
    )
    op.create_index("ix_wagering_bets_account_id", "wagering_bets", ["account_id"])
    op.create_index("ix_wagering_bets_game_id", "wagering_bets", ["game_id"])
    op.create_index("ix_wagering_bets_market_id", "wagering_bets", ["market_id"])


def downgrade() -> None:
    op.drop_index("ix_wagering_bets_market_id", table_name="wagering_bets")
    op.drop_index("ix_wagering_bets_game_id", table_name="wagering_bets")
    op.drop_index("ix_wagering_bets_account_id", table_name="wagering_bets")
    op.drop_table("wagering_bets")
    with op.batch_alter_table("cfb_games") as batch_op:
        batch_op.drop_constraint("ck_game_final_scores_present", type_="check")
        batch_op.drop_constraint("ck_game_scores_nonnegative", type_="check")
        batch_op.drop_constraint("ck_game_status", type_="check")
        batch_op.create_check_constraint("ck_game_status", "status IN ('SCHEDULED')")
        batch_op.drop_column("away_score")
        batch_op.drop_column("home_score")
