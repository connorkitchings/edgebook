"""Persistence models for simulation-only wager positions."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from edgebook.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class BetStatus(str, Enum):
    PENDING = "PENDING"
    WON = "WON"
    LOST = "LOST"
    PUSH = "PUSH"


class Bet(Base):
    """A straight simulated bet with immutable placement snapshots."""

    __tablename__ = "wagering_bets"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "idempotency_key", name="uq_bet_account_idempotency"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    game_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_games.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    market_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_markets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quote_id: Mapped[str] = mapped_column(
        ForeignKey("cfb_market_quotes.id", ondelete="RESTRICT"), nullable=False
    )
    stake_transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    payout_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    selection: Mapped[str] = mapped_column(String(32), nullable=False)
    market_type: Mapped[str] = mapped_column(String(32), nullable=False)
    line_millipoints: Mapped[int | None] = mapped_column(Integer, nullable=True)
    american_odds: Mapped[int] = mapped_column(Integer, nullable=False)
    stake_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    bankroll_before_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    payout_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=BetStatus.PENDING.value
    )
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
