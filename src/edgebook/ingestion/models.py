"""Persistence records for provider provenance and ingestion operations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from edgebook.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class IngestionRun(Base):
    """One idempotent provider sync attempt and its operational outcome."""

    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RUNNING")
    records_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requested_snapshot_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    provider_snapshot_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    quota_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quota_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderEventLink(Base):
    """Stable mapping from a provider event identifier to one canonical game."""

    __tablename__ = "ingestion_provider_event_links"
    __table_args__ = (
        UniqueConstraint(
            "provider", "external_event_id", name="uq_provider_event_link"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    game_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_games.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class BackfillCheckpoint(Base):
    """Durable progress for one requested historical provider snapshot."""

    __tablename__ = "ingestion_backfill_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "sport",
            "markets",
            "bookmakers",
            "requested_snapshot_at",
            name="uq_ingestion_backfill_checkpoint",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(100), nullable=False)
    markets: Mapped[str] = mapped_column(String(200), nullable=False)
    bookmakers: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    requested_snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderObservation(Base):
    """Immutable raw provider record used for provenance and idempotency."""

    __tablename__ = "ingestion_provider_observations"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "scope",
            "external_id",
            "payload_hash",
            name="uq_provider_observation_payload",
        ),
        Index("ix_provider_observation_game", "game_id"),
        Index("ix_provider_observation_provider", "provider"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    game_id: Mapped[str | None] = mapped_column(
        ForeignKey("cfb_games.id", ondelete="RESTRICT"), nullable=True
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
