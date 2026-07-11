"""Add structured reasoning fields to bets.

Revision ID: 20260711_03
Revises: 20260711_02
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260711_03"
down_revision: str | None = "20260711_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("wagering_bets") as batch_op:
        batch_op.add_column(
            sa.Column("rationale_category", sa.String(length=64), nullable=True)
        )
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.create_check_constraint(
            "ck_bet_rationale_category",
            "rationale_category IS NULL OR rationale_category IN "
            "('MATCHUP_ANALYSIS', 'STATISTICAL_EDGE', 'LINE_VALUE', "
            "'INJURY_IMPACT', 'SITUATIONAL', 'CONTRARIAN', 'OTHER')",
        )


def downgrade() -> None:
    with op.batch_alter_table("wagering_bets") as batch_op:
        batch_op.drop_constraint("ck_bet_rationale_category", type_="check")
        batch_op.drop_column("notes")
        batch_op.drop_column("rationale_category")
