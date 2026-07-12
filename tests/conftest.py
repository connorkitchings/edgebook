"""Test fixtures and utilities for the project."""

import tempfile
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from edgebook.core.database import get_db
from edgebook.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db_engine(tmp_path: Path):
    """Create an isolated SQLite database by applying the real migrations."""
    database_path = tmp_path / "edgebook-test.db"
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(alembic_config, "head")

    engine = create_engine(
        f"sqlite:///{database_path}", connect_args={"check_same_thread": False}
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(db_engine):
    """Return a session factory bound to one isolated migrated database."""
    return sessionmaker(
        bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False
    )


@pytest.fixture
def db_session(session_factory) -> Session:
    """Provide a direct database session for service and assertion tests."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    """Provide an API client whose database dependency uses an isolated database."""
    session = session_factory()

    # Create default admin user in test database to bypass authentication
    from edgebook.auth.models import AppUser, UserRole
    from edgebook.auth.services import hash_password
    from edgebook.ledger.services import create_account

    admin = session.query(AppUser).filter(AppUser.username == "default_admin").first()
    if not admin:
        admin_account = create_account(
            session, owner_name="default_admin", starting_bankroll_cents=1000000
        )
        admin = AppUser(
            username="default_admin",
            hashed_password=hash_password("admin_pass"),
            role=UserRole.ADMIN.value,
            account_id=admin_account.id,
        )
        session.add(admin)
        session.commit()

    admin_id = admin.id
    session.close()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user(db: Session = Depends(override_get_db)):
        return db.get(AppUser, admin_id)

    from edgebook.auth.dependencies import get_current_user, get_optional_current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
