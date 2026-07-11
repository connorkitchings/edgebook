"""Add score correction audit table.

Revision ID: 20260711_05
Revises: 20260711_04
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260711_05"
down_revision: str | None = "20260711_04"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cfb_score_corrections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=False),
        sa.Column("original_home_score", sa.Integer(), nullable=False),
        sa.Column("original_away_score", sa.Integer(), nullable=False),
        sa.Column("corrected_home_score", sa.Integer(), nullable=False),
        sa.Column("corrected_away_score", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cfb_score_corrections_game_id",
        "cfb_score_corrections",
        ["game_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cfb_score_corrections_game_id", table_name="cfb_score_corrections"
    )
    op.drop_table("cfb_score_corrections")
