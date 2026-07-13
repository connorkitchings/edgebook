"""Main entry point for Edgebook FastAPI application."""

from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app
from sqlalchemy.orm import Session

from edgebook import __version__
from edgebook.api.accounts import router as accounts_router
from edgebook.api.analytics import router as analytics_router
from edgebook.api.auth import router as auth_router
from edgebook.api.cfb import router as cfb_router
from edgebook.api.ingestion import router as ingestion_router
from edgebook.api.pages import router as pages_router
from edgebook.api.reviews import router as reviews_router
from edgebook.api.wagering import router as wagering_router
from edgebook.core.config import settings
from edgebook.core.database import check_db_health, get_db
from edgebook.observability.metrics import DB_UP, HTTP_REQUESTS
from edgebook.utils.logging import setup_logging

# Configure logging at application startup
setup_logging(
    level="INFO",
    log_file="/app/logs/edgebook.log" if settings.ENV == "production" else None,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="College Football Paper-Betting Platform API",
    version=__version__,
)


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
def custom_unauthorized_handler(
    request: Request, exc: Exception
) -> RedirectResponse | Response:
    """Redirect HTML page requests to login upon authentication failure."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept or request.url.path == "/":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Return default JSON error response
    from fastapi.responses import JSONResponse

    detail = getattr(exc, "detail", "Not authenticated")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
    )


@app.middleware("http")
async def record_http_request(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Count every HTTP request so /metrics can expose traffic by route."""
    try:
        response = await call_next(request)
    except Exception:
        route = request.scope.get("route")
        path = getattr(route, "path", None) or "unmatched"
        HTTP_REQUESTS.labels(
            method=request.method,
            path_template=path,
            status="500",
        ).inc()
        raise

    route = request.scope.get("route")
    path = getattr(route, "path", None) or "unmatched"
    HTTP_REQUESTS.labels(
        method=request.method,
        path_template=path,
        status=str(response.status_code),
    ).inc()
    return response


app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(accounts_router)
app.include_router(cfb_router)
app.include_router(wagering_router)
app.include_router(reviews_router)
app.include_router(analytics_router)
app.include_router(ingestion_router)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Prometheus metrics endpoint. Mounted sub-apps are excluded from the OpenAPI
# schema, so /metrics does not appear in /docs.
app.mount("/metrics", make_asgi_app())


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


@app.get("/healthz")
def liveness() -> dict[str, str]:
    """Liveness probe: the process is up and serving requests."""
    return {"status": "alive"}


@app.get("/readyz")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness probe: the application database is reachable.

    Updates the ``edgebook_db_up`` gauge so scrapes reflect the latest check.
    """
    db_ok = check_db_health(db)
    DB_UP.set(1 if db_ok else 0)
    return {
        "status": "ok" if db_ok else "unhealthy",
        "database": "ok" if db_ok else "down",
    }
