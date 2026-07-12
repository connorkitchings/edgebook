"""Authentication and session management services."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from sqlalchemy.orm import Session

from edgebook.auth.models import AppUser, UserRole
from edgebook.core.config import settings
from edgebook.ledger.services import create_account


def base64url_encode(data: bytes) -> str:
    """Encode bytes to base64url format string."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64url_decode(data: str) -> bytes:
    """Decode base64url format string to bytes."""
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    """Hash a password using standard PBKDF2 with SHA256."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its PBKDF2 hash."""
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False


def encode_jwt(payload: dict[str, Any], expires_in_seconds: int = 86400) -> str:
    """Generate a signed HS256 JWT token using standard libraries."""
    header = {"alg": "HS256", "typ": "JWT"}

    # Add expiration time to payload
    token_payload = payload.copy()
    token_payload["exp"] = int(time.time()) + expires_in_seconds

    header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(token_payload).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt(token: str) -> dict[str, Any] | None:
    """Decode and verify a signed HS256 JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        expected_signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()

        if not hmac.compare_digest(base64url_decode(signature_b64), expected_signature):
            return None

        payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))

        # Verify expiration
        if "exp" in payload and payload["exp"] < time.time():
            return None

        return payload
    except Exception:
        return None


def create_user(
    db: Session,
    username: str,
    password: str,
    role: UserRole | str = UserRole.USER,
    starting_bankroll_cents: int = 1000000,
) -> AppUser:
    """Atomically create a user and their double-entry ledger account."""
    normalized_username = username.strip().lower()
    if not normalized_username:
        raise ValueError("Username cannot be blank")

    # Check if user already exists
    existing = db.query(AppUser).filter(AppUser.username == normalized_username).first()
    if existing:
        raise ValueError(f"Username '{username}' is already taken")

    # Start nested transaction to ensure atomicity
    try:
        # 1. Create the ledger account
        account = create_account(
            db,
            owner_name=username,
            starting_bankroll_cents=starting_bankroll_cents,
        )

        # 2. Hash password and save user
        hashed = hash_password(password)
        user = AppUser(
            username=normalized_username,
            hashed_password=hashed,
            role=role.value if isinstance(role, UserRole) else str(role),
            account_id=account.id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as error:
        db.rollback()
        raise error


def authenticate_user(db: Session, username: str, password: str) -> AppUser | None:
    """Authenticate a user by username and password."""
    normalized_username = username.strip().lower()
    user = db.query(AppUser).filter(AppUser.username == normalized_username).first()
    if not user:
        return None

    if verify_password(password, user.hashed_password):
        return user
    return None
