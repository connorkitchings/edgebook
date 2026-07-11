"""Add multi-source ingestion provenance and human review workflow.

Revision ID: 20260711_07
Revises: 20260711_06
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260711_07"
down_revision: str | None = "20260711_06"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("records_created", sa.Integer(), nullable=False),
        sa.Column("records_skipped", sa.Integer(), nullable=False),
        sa.Column("conflict_count", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_provider", "ingestion_runs", ["provider"])
    op.create_table(
        "ingestion_provider_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "scope",
            "external_id",
            "payload_hash",
            name="uq_provider_observation_payload",
        ),
    )
    op.create_index(
        "ix_provider_observation_game", "ingestion_provider_observations", ["game_id"]
    )
    op.create_index(
        "ix_provider_observation_provider",
        "ingestion_provider_observations",
        ["provider"],
    )
    with op.batch_alter_table("cfb_games") as batch_op:
        batch_op.add_column(
            sa.Column(
                "score_sync_state",
                sa.String(length=32),
                nullable=False,
                server_default="UNCONFIRMED",
            )
        )
    with op.batch_alter_table("cfb_market_quotes") as batch_op:
        batch_op.drop_constraint("uq_quote_market_selection", type_="unique")
        batch_op.add_column(sa.Column("source", sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column("source_quote_id", sa.String(length=200), nullable=True)
        )
        batch_op.add_column(
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_quote_market_selection_source",
            ["market_id", "selection", "source", "source_quote_id"],
        )
    op.create_index("ix_cfb_market_quotes_source", "cfb_market_quotes", ["source"])
    op.create_table(
        "cfb_score_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_event_id", sa.String(length=200), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "game_id",
            "source",
            "source_event_id",
            "home_score",
            "away_score",
            name="uq_score_observation_identity",
        ),
    )
    op.create_index("ix_score_observations_game", "cfb_score_observations", ["game_id"])
    op.create_table(
        "cfb_score_resolutions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("game_id", sa.String(length=36), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("resolved_by", sa.String(length=200), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["cfb_games.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_score_resolutions_game", "cfb_score_resolutions", ["game_id"])
    with op.batch_alter_table("wagering_bets") as batch_op:
        batch_op.add_column(
            sa.Column("quote_source", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("quote_source_id", sa.String(length=200), nullable=True)
        )
        batch_op.add_column(
            sa.Column("quote_observed_at", sa.DateTime(timezone=True), nullable=True)
        )
    op.create_table(
        "wagering_bet_reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("bet_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_label", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("bias_flags", sa.Text(), nullable=True),
        sa.Column("assessment_notes", sa.Text(), nullable=True),
        sa.Column("review_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["bet_id"], ["wagering_bets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bet_id"),
    )
    op.create_index("ix_wagering_bet_reviews_bet", "wagering_bet_reviews", ["bet_id"])


def downgrade() -> None:
    op.drop_index("ix_wagering_bet_reviews_bet", table_name="wagering_bet_reviews")
    op.drop_table("wagering_bet_reviews")
    with op.batch_alter_table("wagering_bets") as batch_op:
        batch_op.drop_column("quote_observed_at")
        batch_op.drop_column("quote_source_id")
        batch_op.drop_column("quote_source")
    op.drop_index("ix_score_resolutions_game", table_name="cfb_score_resolutions")
    op.drop_table("cfb_score_resolutions")
    op.drop_index("ix_score_observations_game", table_name="cfb_score_observations")
    op.drop_table("cfb_score_observations")
    op.drop_index("ix_cfb_market_quotes_source", table_name="cfb_market_quotes")
    with op.batch_alter_table("cfb_market_quotes") as batch_op:
        batch_op.drop_constraint("uq_quote_market_selection_source", type_="unique")
        batch_op.drop_column("observed_at")
        batch_op.drop_column("source_quote_id")
        batch_op.drop_column("source")
        batch_op.create_unique_constraint(
            "uq_quote_market_selection", ["market_id", "selection"]
        )
    with op.batch_alter_table("cfb_games") as batch_op:
        batch_op.drop_column("score_sync_state")
    op.drop_index(
        "ix_provider_observation_provider", table_name="ingestion_provider_observations"
    )
    op.drop_index(
        "ix_provider_observation_game", table_name="ingestion_provider_observations"
    )
    op.drop_table("ingestion_provider_observations")
    op.drop_index("ix_ingestion_runs_provider", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
