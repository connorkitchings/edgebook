"""Tests for database connectivity and health checks."""

from edgebook.core.database import SessionLocal, check_db_health


def test_database_health():
    """Verify that checking db health works on a live session."""
    db = SessionLocal()
    try:
        assert check_db_health(db) is True
    finally:
        db.close()
