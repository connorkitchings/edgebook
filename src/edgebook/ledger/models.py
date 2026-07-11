"""SQLAlchemy models for the generic Edgebook ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from edgebook.core.database import Base


class AccountKind(str, Enum):
    """Classifies ledger accounts without coupling them to a product domain."""

    USER_ASSET = "USER_ASSET"
    EQUITY = "EQUITY"


class TransactionType(str, Enum):
    """Economic event categories supported by the ledger."""

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    WAGER_STAKE = "WAGER_STAKE"
    WAGER_PAYOUT = "WAGER_PAYOUT"
    ADJUSTMENT = "ADJUSTMENT"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class Account(Base):
    """A generic ledger account with a materialized simulation-credit balance."""

    __tablename__ = "ledger_accounts"
    __table_args__ = (
        CheckConstraint(
            "starting_bankroll_cents >= 0", name="ck_account_starting_nonnegative"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    owner_name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[AccountKind] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    starting_bankroll_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    current_balance_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")


class JournalEntry(Base):
    """Immutable grouping for a balanced set of ledger transaction postings."""

    __tablename__ = "ledger_journal_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="journal_entry"
    )


class Transaction(Base):
    """An immutable signed posting within a balanced journal entry."""

    __tablename__ = "ledger_transactions"
    __table_args__ = (
        CheckConstraint("amount_cents != 0", name="ck_transaction_amount_nonzero"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    journal_entry_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_journal_entries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        String(32), nullable=False
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    account: Mapped[Account] = relationship(back_populates="transactions")
    journal_entry: Mapped[JournalEntry] = relationship(back_populates="transactions")
