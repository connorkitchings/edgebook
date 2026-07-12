"""Add production odds ingestion operations.

Revision ID: e73c908b42db
Revises: 20260711_07
Create Date: 2026-07-12 09:06:34.643065
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e73c908b42db"
down_revision: str | None = "20260711_07"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_backfill_checkpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("sport", sa.String(length=100), nullable=False),
        sa.Column("markets", sa.String(length=200), nullable=False),
        sa.Column("bookmakers", sa.String(length=500), nullable=False),
        sa.Column("requested_snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "sport",
            "markets",
            "bookmakers",
            "requested_snapshot_at",
            name="uq_ingestion_backfill_checkpoint",
        ),
    )
    op.create_index(
        op.f("ix_ingestion_backfill_checkpoints_provider"),
        "ingestion_backfill_checkpoints",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_backfill_checkpoints_run_id"),
        "ingestion_backfill_checkpoints",
        ["run_id"],
        unique=False,
    )
    op.create_table(
        "ingestion_provider_event_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("external_event_id", sa.String(length=200), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider", "external_event_id", name="uq_provider_event_link"
        ),
    )
    op.create_index(
        op.f("ix_ingestion_provider_event_links_game_id"),
        "ingestion_provider_event_links",
        ["game_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_provider_event_links_provider"),
        "ingestion_provider_event_links",
        ["provider"],
        unique=False,
    )
    with op.batch_alter_table("cfb_market_quotes") as batch_op:
        batch_op.add_column(
            sa.Column("source_event_id", sa.String(length=200), nullable=True)
        )
        batch_op.create_index(
            "ix_cfb_market_quotes_market_observed", ["market_id", "observed_at"]
        )
        batch_op.create_index(
            "ix_cfb_market_quotes_source_observed", ["source", "observed_at"]
        )
    op.create_index(
        op.f("ix_ingestion_provider_observations_run_id"),
        "ingestion_provider_observations",
        ["run_id"],
        unique=False,
    )
    with op.batch_alter_table("ingestion_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "requested_snapshot_at", sa.DateTime(timezone=True), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column("provider_snapshot_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("quota_used", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("quota_remaining", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ingestion_runs") as batch_op:
        batch_op.drop_column("quota_remaining")
        batch_op.drop_column("quota_used")
        batch_op.drop_column("provider_snapshot_at")
        batch_op.drop_column("requested_snapshot_at")
    op.drop_index(
        op.f("ix_ingestion_provider_observations_run_id"),
        table_name="ingestion_provider_observations",
    )
    with op.batch_alter_table("cfb_market_quotes") as batch_op:
        batch_op.drop_index("ix_cfb_market_quotes_source_observed")
        batch_op.drop_index("ix_cfb_market_quotes_market_observed")
        batch_op.drop_column("source_event_id")
    op.drop_index(
        op.f("ix_ingestion_provider_event_links_provider"),
        table_name="ingestion_provider_event_links",
    )
    op.drop_index(
        op.f("ix_ingestion_provider_event_links_game_id"),
        table_name="ingestion_provider_event_links",
    )
    op.drop_table("ingestion_provider_event_links")
    op.drop_index(
        op.f("ix_ingestion_backfill_checkpoints_run_id"),
        table_name="ingestion_backfill_checkpoints",
    )
    op.drop_index(
        op.f("ix_ingestion_backfill_checkpoints_provider"),
        table_name="ingestion_backfill_checkpoints",
    )
    op.drop_table("ingestion_backfill_checkpoints")
