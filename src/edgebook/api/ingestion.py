"""FastAPI routes for provider ingestion sync and conflict resolution."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from edgebook.core.database import get_db
from edgebook.ingestion.adapters import load_normalized_feed
from edgebook.ingestion.services import (
    IngestionConflictError,
    IngestionError,
    IngestionNotFoundError,
    list_conflicts,
    list_runs,
    resolve_score_conflict,
    settle_confirmed_games,
    sync_games,
    sync_quotes,
    sync_scores,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

FIXTURE_FEED_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "processed" / "fixture_feed.json"
)


def _load_fixture_adapter():
    """Load the fixture feed adapter for local development sync triggers."""
    if not FIXTURE_FEED_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fixture feed not found at {FIXTURE_FEED_PATH}",
        )
    return load_normalized_feed(FIXTURE_FEED_PATH, provider="fixture")


class SyncResponse(BaseModel):
    run_id: str
    status: str
    seen: int
    created: int
    skipped: int
    conflicts: int


class SettleResponse(BaseModel):
    settled_count: int


class ConflictGameResponse(BaseModel):
    game_id: str
    home_team: str
    away_team: str
    scheduled_at: str
    score_sync_state: str

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    id: str
    provider: str
    scope: str
    status: str
    records_seen: int
    records_created: int
    records_skipped: int
    conflict_count: int
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class RunPage(BaseModel):
    items: list[RunResponse]
    total: int
    limit: int
    offset: int


class ConflictResolutionCreate(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=1000)
    resolved_by: str = Field(min_length=1, max_length=200)


class ConflictResolutionResponse(BaseModel):
    game_id: str
    home_score: int
    away_score: int
    reason: str
    resolved_by: str
    resolved_at: str


def raise_ingestion_http_error(error: Exception) -> None:
    if isinstance(error, IngestionNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, IngestionConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, IngestionError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    raise error


@router.post("/sync/games", response_model=SyncResponse)
def sync_games_endpoint(db: Session = Depends(get_db)) -> SyncResponse:
    """Trigger a game sync from the fixture feed."""
    adapter = _load_fixture_adapter()
    try:
        result = sync_games(db, adapter)
    except Exception as error:
        raise_ingestion_http_error(error)
    return SyncResponse(**result)


@router.post("/sync/quotes", response_model=SyncResponse)
def sync_quotes_endpoint(db: Session = Depends(get_db)) -> SyncResponse:
    """Trigger a quotes sync from the fixture feed."""
    adapter = _load_fixture_adapter()
    try:
        result = sync_quotes(db, adapter)
    except Exception as error:
        raise_ingestion_http_error(error)
    return SyncResponse(**result)


@router.post("/sync/scores", response_model=SyncResponse)
def sync_scores_endpoint(db: Session = Depends(get_db)) -> SyncResponse:
    """Trigger a scores sync from the fixture feed."""
    adapter = _load_fixture_adapter()
    try:
        result = sync_scores(db, adapter)
    except Exception as error:
        raise_ingestion_http_error(error)
    return SyncResponse(**result)


@router.post("/settle", response_model=SettleResponse)
def settle_endpoint(db: Session = Depends(get_db)) -> SettleResponse:
    """Settle all games with confirmed score agreement."""
    try:
        count = settle_confirmed_games(db)
    except Exception as error:
        raise_ingestion_http_error(error)
    return SettleResponse(settled_count=count)


@router.get("/runs", response_model=RunPage)
def list_runs_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> RunPage:
    """List ingestion run history newest-first."""
    runs, total = list_runs(db, limit=limit, offset=offset)
    return RunPage(
        items=[RunResponse.model_validate(r) for r in runs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/conflicts", response_model=list[ConflictGameResponse])
def list_conflicts_endpoint(
    db: Session = Depends(get_db),
) -> list[ConflictGameResponse]:
    """List all games with conflicted score sync state."""
    games = list_conflicts(db)
    return [
        ConflictGameResponse(
            game_id=g.id,
            home_team=g.home_team.name if g.home_team else "Unknown",
            away_team=g.away_team.name if g.away_team else "Unknown",
            scheduled_at=g.scheduled_at.isoformat(),
            score_sync_state=g.score_sync_state,
        )
        for g in games
    ]


@router.post(
    "/conflicts/{game_id}/resolve",
    response_model=ConflictResolutionResponse,
)
def resolve_conflict_endpoint(
    game_id: str,
    payload: ConflictResolutionCreate,
    db: Session = Depends(get_db),
) -> ConflictResolutionResponse:
    """Resolve a score conflict for a specific game."""
    try:
        resolution = resolve_score_conflict(
            db,
            game_id=game_id,
            home_score=payload.home_score,
            away_score=payload.away_score,
            reason=payload.reason,
            resolved_by=payload.resolved_by,
        )
    except Exception as error:
        raise_ingestion_http_error(error)
    return ConflictResolutionResponse(
        game_id=resolution.game_id,
        home_score=resolution.home_score,
        away_score=resolution.away_score,
        reason=resolution.reason,
        resolved_by=resolution.resolved_by,
        resolved_at=resolution.resolved_at.isoformat(),
    )
