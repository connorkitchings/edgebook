"""Tests for authentication services and helper functions."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from edgebook.auth.models import UserRole
from edgebook.auth.services import (
    authenticate_user,
    create_user,
    decode_jwt,
    encode_jwt,
    hash_password,
    verify_password,
)
from edgebook.ledger.models import Account


def test_password_hashing() -> None:
    """Password hashing should produce secure hashes that verify correctly."""
    password = "secure_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert ":" in hashed

    # Verification should succeed
    assert verify_password(password, hashed) is True

    # Verification should fail with wrong password
    assert verify_password("wrong_password", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_flow() -> None:
    """JWT tokens should encode payloads and decode/verify them correctly."""
    payload = {"sub": "testuser", "role": "USER"}
    token = encode_jwt(payload, expires_in_seconds=60)

    assert token is not None
    assert len(token.split(".")) == 3

    decoded = decode_jwt(token)
    assert decoded is not None
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "USER"
    assert "exp" in decoded


def test_jwt_token_expiry() -> None:
    """Expired JWT tokens should fail verification."""
    payload = {"sub": "testuser"}
    # Token with 0 seconds life span (immediately expired)
    token = encode_jwt(payload, expires_in_seconds=-5)

    decoded = decode_jwt(token)
    assert decoded is None


def test_jwt_token_tampering() -> None:
    """Tampered JWT tokens should fail signature verification."""
    payload = {"sub": "testuser"}
    token = encode_jwt(payload, expires_in_seconds=60)

    parts = token.split(".")
    # Tamper with signature
    tampered_token = f"{parts[0]}.{parts[1]}.invalid_signature"
    assert decode_jwt(tampered_token) is None


def test_create_user_and_ledger_account(db_session: Session) -> None:
    """create_user should atomically register user and ledger account."""
    user = create_user(
        db_session,
        username="bettor1",
        password="password123",
        role=UserRole.USER,
        starting_bankroll_cents=500000,
    )

    assert user.id is not None
    assert user.username == "bettor1"
    assert user.role == "USER"
    assert user.account_id is not None

    # Assert associated ledger account exists
    account = db_session.get(Account, user.account_id)
    assert account is not None
    assert account.owner_name == "bettor1"
    assert account.starting_bankroll_cents == 500000
    assert account.current_balance_cents == 500000


def test_create_user_duplicate_username(db_session: Session) -> None:
    """Creating a duplicate user should raise an exception and fail atomically."""
    create_user(db_session, username="duplicate", password="password1")

    with pytest.raises(ValueError, match="already taken"):
        create_user(db_session, username="duplicate", password="password1")


def test_create_user_empty_username(db_session: Session) -> None:
    """create_user should reject empty username strings."""
    with pytest.raises(ValueError, match="cannot be blank"):
        create_user(db_session, username="  ", password="password1")


def test_authenticate_user_success_and_failure(db_session: Session) -> None:
    """authenticate_user should return the user on correct credentials."""
    create_user(db_session, username="auth_test", password="mypassword")

    # Success
    user = authenticate_user(db_session, username="auth_test", password="mypassword")
    assert user is not None
    assert user.username == "auth_test"

    # Failure - wrong password
    assert (
        authenticate_user(db_session, username="auth_test", password="wrongpassword")
        is None
    )

    # Failure - wrong username
    assert (
        authenticate_user(db_session, username="nonexistent", password="mypassword")
        is None
    )
