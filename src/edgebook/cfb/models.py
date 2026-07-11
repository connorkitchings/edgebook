"""SQLAlchemy models for the college-football domain boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from edgebook.core.database import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class GameStatus(str, Enum):
    """Lifecycle state supported for manual game intake."""

    SCHEDULED = "SCHEDULED"
    FINAL = "FINAL"


class ScoreSyncState(str, Enum):
    """External-score confidence state used before automated settlement."""

    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    CONFLICTED = "CONFLICTED"
    RESOLVED = "RESOLVED"


class SportType(str, Enum):
    """Supported sport categories. CFB is the initial sport; others may follow."""

    CFB = "CFB"


class MarketType(str, Enum):
    """Supported college-football market categories."""

    SPREAD = "SPREAD"
    MONEYLINE = "MONEYLINE"
    TOTAL = "TOTAL"


class MarketStatus(str, Enum):
    """Whether a market has the quotes needed for future wagering."""

    DRAFT = "DRAFT"
    OPEN = "OPEN"


class MarketSelection(str, Enum):
    """The available outcome selections across the supported market types."""

    HOME = "HOME"
    AWAY = "AWAY"
    OVER = "OVER"
    UNDER = "UNDER"


class Team(Base):
    """A reusable college-football team catalog entry."""

    __tablename__ = "cfb_teams"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class Game(Base):
    """A scheduled contest between two distinct teams."""

    __tablename__ = "cfb_games"
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_game_distinct_teams"),
        CheckConstraint("sport IN ('CFB')", name="ck_game_sport"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    sport: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SportType.CFB.value
    )
    home_team_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_teams.id"), nullable=False, index=True
    )
    away_team_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_teams.id"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[GameStatus] = mapped_column(
        String(32), nullable=False, default=GameStatus.SCHEDULED.value
    )
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_sync_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ScoreSyncState.UNCONFIRMED.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])
    markets: Mapped[list[Market]] = relationship(back_populates="game")


class Market(Base):
    """A manual market line for one game and market type.

    Multiple markets of the same type may exist for a game when they have
    different lines (e.g., alternate spreads). Moneyline markets have a
    NULL line and are limited to one per game via the service layer.
    """

    __tablename__ = "cfb_markets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    game_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_games.id"), nullable=False, index=True
    )
    market_type: Mapped[MarketType] = mapped_column(String(32), nullable=False)
    line_millipoints: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[MarketStatus] = mapped_column(
        String(32), nullable=False, default=MarketStatus.DRAFT.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    game: Mapped[Game] = relationship(back_populates="markets")
    quotes: Mapped[list[MarketQuote]] = relationship(back_populates="market")


class MarketQuote(Base):
    """An immutable manual or provider-specific American-odds observation."""

    __tablename__ = "cfb_market_quotes"
    __table_args__ = (
        UniqueConstraint(
            "market_id",
            "selection",
            "source",
            "source_quote_id",
            name="uq_quote_market_selection_source",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    market_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_markets.id"), nullable=False, index=True
    )
    selection: Mapped[MarketSelection] = mapped_column(String(32), nullable=False)
    american_odds: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_quote_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    market: Mapped[Market] = relationship(back_populates="quotes")


class ScoreObservation(Base):
    """An immutable final-score observation reported by one data provider."""

    __tablename__ = "cfb_score_observations"
    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "source",
            "source_event_id",
            "home_score",
            "away_score",
            name="uq_score_observation_identity",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    game_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_games.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScoreResolution(Base):
    """Operator decision that resolves a held external-score conflict."""

    __tablename__ = "cfb_score_resolutions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    game_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_games.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_by: Mapped[str] = mapped_column(String(200), nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class ScoreCorrection(Base):
    """An audit-trail record for a corrected final score.

    Each correction stores the original and corrected scores along with a
    required reason. The correction process reverses prior payout postings
    via offsetting ADJUSTMENT entries and re-settles all bets atomically.
    """

    __tablename__ = "cfb_score_corrections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    game_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_games.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    original_home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    original_away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    corrected_home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    corrected_away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
