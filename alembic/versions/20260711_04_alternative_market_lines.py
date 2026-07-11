"""Relax market uniqueness to allow alternative lines.

Revision ID: 20260711_04
Revises: 20260711_03
Create Date: 2026-07-11
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260711_04"
down_revision: str | None = "20260711_03"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("cfb_markets") as batch_op:
        batch_op.drop_constraint("uq_market_game_type", type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("cfb_markets") as batch_op:
        batch_op.create_unique_constraint(
            "uq_market_game_type", ["game_id", "market_type"]
        )
