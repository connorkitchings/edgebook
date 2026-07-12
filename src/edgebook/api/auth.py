"""API router for authentication and session management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from edgebook.auth.services import authenticate_user, create_user, encode_jwt
from edgebook.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """Token response payload for JSON-based login/signup."""

    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class LoginPayload(BaseModel):
    """Login payload for JSON-based requests."""

    username: str
    password: str


class RegisterPayload(BaseModel):
    """Registration payload for JSON-based requests."""

    username: str
    password: str
    starting_bankroll_cents: int = 1000000


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
def register_user_json(
    payload: RegisterPayload,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new user via JSON and get an auth token."""
    try:
        user = create_user(
            db,
            username=payload.username,
            password=payload.password,
            starting_bankroll_cents=payload.starting_bankroll_cents,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    token = encode_jwt({"sub": user.username})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login_user_json(
    payload: LoginPayload,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user via JSON and set/get an auth token."""
    user = authenticate_user(db, username=payload.username, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = encode_jwt({"sub": user.username})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
    )


@router.post("/logout")
def logout_user(response: Response) -> dict[str, str]:
    """Log out the current user by clearing the session cookie."""
    response.delete_cookie("session_token")
    return {"status": "success", "message": "Successfully logged out"}
