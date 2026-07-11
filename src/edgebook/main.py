"""Main entry point for Edgebook FastAPI application."""

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from edgebook.api.accounts import router as accounts_router
from edgebook.api.analytics import router as analytics_router
from edgebook.api.cfb import router as cfb_router
from edgebook.api.wagering import router as wagering_router
from edgebook.core.config import settings
from edgebook.core.database import check_db_health, get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="College Football Paper-Betting Platform API",
    version="0.1.0",
)

app.include_router(accounts_router)
app.include_router(cfb_router)
app.include_router(wagering_router)
app.include_router(analytics_router)


@app.get("/")
def read_root():
    """Welcome root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "environment": settings.ENV,
        "debug": settings.DEBUG,
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying API and database connectivity.

    Args:
        db: Database session dependency

    Returns:
        Dictionary indicating status of API and database services
    """
    db_ok = check_db_health(db)
    status = "ok" if db_ok else "unhealthy"

    return {
        "status": status,
        "services": {
            "api": "ok",
            "database": "ok" if db_ok else "down",
        },
    }
