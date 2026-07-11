"""Add sport column to cfb_games.

Revision ID: 20260711_06
Revises: 20260711_05
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260711_06"
down_revision: str | None = "20260711_05"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cfb_games") as batch_op:
        batch_op.add_column(
            sa.Column(
                "sport",
                sa.String(length=32),
                nullable=False,
                server_default="CFB",
            )
        )
        batch_op.create_check_constraint(
            "ck_game_sport",
            "sport IN ('CFB')",
        )


def downgrade() -> None:
    with op.batch_alter_table("cfb_games") as batch_op:
        batch_op.drop_constraint("ck_game_sport", type_="check")
        batch_op.drop_column("sport")
