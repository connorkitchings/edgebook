"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from edgebook.auth.models import AppUser, UserRole
from edgebook.auth.services import decode_jwt
from edgebook.core.database import get_db


def get_token_from_request(request: Request) -> str | None:
    """Extract the JWT token from cookies or the Authorization header."""
    # 1. Try cookie first
    token = request.cookies.get("session_token")
    if token:
        return token

    # 2. Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> AppUser:
    """Retrieve the currently authenticated user. Raises 401 if unauthenticated."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_jwt(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    username = payload["sub"]
    user = db.query(AppUser).filter(AppUser.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> AppUser | None:
    """Retrieve the currently authenticated user, returning None if unauthenticated."""
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


class RoleChecker:
    """Dependency checker to enforce role-based access control."""

    def __init__(self, allowed_roles: list[UserRole | str]) -> None:
        self.allowed_roles = [
            r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles
        ]

    def __call__(self, current_user: AppUser = Depends(get_current_user)) -> AppUser:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Insufficient privileges",
            )
        return current_user


def require_role(allowed_roles: list[UserRole | str]) -> RoleChecker:
    """Return a dependency checker that enforces specific user roles."""
    return RoleChecker(allowed_roles)
