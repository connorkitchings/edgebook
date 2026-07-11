"""Main entry point for Edgebook FastAPI application."""

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from edgebook.api.accounts import router as accounts_router
from edgebook.api.analytics import router as analytics_router
from edgebook.api.cfb import router as cfb_router
from edgebook.api.ingestion import router as ingestion_router
from edgebook.api.pages import router as pages_router
from edgebook.api.wagering import router as wagering_router
from edgebook.core.config import settings
from edgebook.core.database import check_db_health, get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="College Football Paper-Betting Platform API",
    version="0.1.0",
)

app.include_router(pages_router)
app.include_router(accounts_router)
app.include_router(cfb_router)
app.include_router(wagering_router)
app.include_router(analytics_router)
app.include_router(ingestion_router)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
