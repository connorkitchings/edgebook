"""Database connectivity and session setup for Edgebook."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from edgebook.core.config import settings

# Create database engine
# SQLite requires check_same_thread=False
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# Session maker factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """Database session dependency for routes.

    Yields:
        db: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health(db) -> bool:
    """Run SELECT 1 to verify database connection health.

    Args:
        db: Database session

    Returns:
        True if database responds successfully, False otherwise
    """
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
