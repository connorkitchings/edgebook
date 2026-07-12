"""Integration tests for auth and role protection endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from edgebook.auth.models import UserRole
from edgebook.auth.services import create_user, encode_jwt
from edgebook.core.database import get_db
from edgebook.main import app


@pytest.fixture
def client(session_factory) -> TestClient:
    """Local client fixture that does not mock authentication dependencies."""

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_auth_json_register_and_login_flow(client: TestClient) -> None:
    """Register and login JSON flow should return tokens and set cookies."""
    # 1. Register
    reg_response = client.post(
        "/auth/register",
        json={
            "username": "apiuser1",
            "password": "apipassword",
            "starting_bankroll_cents": 1000000,
        },
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["username"] == "apiuser1"
    assert "access_token" in reg_data
    assert "session_token" in client.cookies

    # Clear cookies for login test
    client.cookies.clear()

    # 2. Login
    login_response = client.post(
        "/auth/login",
        json={"username": "apiuser1", "password": "apipassword"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["username"] == "apiuser1"
    assert "access_token" in login_data
    assert "session_token" in client.cookies

    # 3. Logout
    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200
    # Cookie should be cleared (either deleted or empty value)
    assert (
        "session_token" not in client.cookies
        or client.cookies.get("session_token") == ""
    )


def test_auth_login_failure(client: TestClient, db_session: Session) -> None:
    """Login should fail with 401 when given incorrect credentials."""
    create_user(db_session, username="failuser", password="validpassword")

    response = client.post(
        "/auth/login",
        json={"username": "failuser", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_unauthenticated_request_raises_401(client: TestClient) -> None:
    """Accessing protected routes without a token/cookie should return 401."""
    # Protected account endpoint
    response = client.get("/accounts/some-id")
    assert response.status_code == 401


def test_user_authorization_ownership_boundaries(
    client: TestClient, db_session: Session
) -> None:
    """A standard USER role can only access their own account and wagers."""
    user1 = create_user(db_session, username="user1", password="pass")
    user2 = create_user(db_session, username="user2", password="pass")

    token1 = encode_jwt({"sub": user1.username})

    # User 1 requesting User 1's account -> OK (since it returns 200)
    client.cookies.set("session_token", token1)
    response_self = client.get(f"/accounts/{user1.account_id}")
    assert response_self.status_code == 200

    # User 1 requesting User 2's account -> 403 Forbidden
    response_other = client.get(f"/accounts/{user2.account_id}")
    assert response_other.status_code == 403
    assert "Forbidden" in response_other.json()["detail"]

    # User 1 requesting User 1's bets page -> OK (returns 200)
    response_bets_self = client.get(f"/accounts/{user1.account_id}/bets")
    assert response_bets_self.status_code == 200

    # User 1 requesting User 2's bets page -> 403 Forbidden
    response_bets_other = client.get(f"/accounts/{user2.account_id}/bets")
    assert response_bets_other.status_code == 403


def test_admin_authorization_unrestricted(
    client: TestClient, db_session: Session
) -> None:
    """An ADMIN role can access other accounts, logs, and settle scores."""
    user1 = create_user(db_session, username="user1", password="pass")
    admin1 = create_user(
        db_session, username="admin1", password="pass", role=UserRole.ADMIN
    )

    admin_token = encode_jwt({"sub": admin1.username})
    client.cookies.set("session_token", admin_token)

    # Admin requests User 1's account details -> 200 OK
    response_other = client.get(f"/accounts/{user1.account_id}")
    assert response_other.status_code == 200

    # Admin requests ingestion runs list -> 200 OK
    response_ingest = client.get("/ingestion/runs")
    assert response_ingest.status_code == 200

    # Admin resolves score conflict -> should bypass auth check
    # (and hit 404 since game is mock/non-existent)
    response_resolve = client.post(
        "/ingestion/conflicts/nonexistent-game-id/resolve",
        json={
            "home_score": 10,
            "away_score": 7,
            "reason": "Correcting error",
            "resolved_by": "admin1",
        },
    )
    assert response_resolve.status_code in (404, 422)  # Auth bypassed


def test_operator_reviews_access(client: TestClient, db_session: Session) -> None:
    """An OPERATOR role can access reviews queue, but not ingestion pages."""
    operator = create_user(
        db_session, username="op1", password="pass", role=UserRole.OPERATOR
    )
    user = create_user(db_session, username="user1", password="pass")

    op_token = encode_jwt({"sub": operator.username})
    user_token = encode_jwt({"sub": user.username})

    # User attempts to access reviews -> 403 Forbidden
    client.cookies.set("session_token", user_token)
    response_user = client.get("/reviews")
    assert response_user.status_code == 403

    # Operator attempts to access reviews -> 200 OK
    client.cookies.set("session_token", op_token)
    response_op = client.get("/reviews")
    assert response_op.status_code == 200

    # Operator attempts to access ingestion runs -> 403 Forbidden
    response_ingest = client.get("/ingestion/runs")
    assert response_ingest.status_code == 403
