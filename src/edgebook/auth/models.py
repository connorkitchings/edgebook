"""Database models for authentication and user accounts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from edgebook.core.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(UTC)


class UserRole(str, Enum):
    """Roles representing user access privileges."""

    USER = "USER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class AppUser(Base):
    """System user with credentials and role-based permissions."""

    __tablename__ = "auth_users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default=UserRole.USER.value
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    # Use a string relationship reference to avoid circular imports.
    account: Mapped[object] = relationship(
        "Account", foreign_keys=[account_id], lazy="joined"
    )
