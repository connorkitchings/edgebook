"""FastAPI routes for manual college-football game and odds intake."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from edgebook.application.operations import resolve_score_conflict
from edgebook.cfb.models import (
    Game,
    Market,
    MarketQuote,
    MarketSelection,
    MarketStatus,
    MarketType,
    ScoreSyncState,
    SportType,
    Team,
)
from edgebook.cfb.services import (
    CfbConflictError,
    CfbNotFoundError,
    CfbValidationError,
    create_game,
    create_market,
    create_quote,
    create_team,
    get_game,
    list_games,
    odds_history,
    quote_comparison,
)
from edgebook.core.database import get_db
from edgebook.ingestion.services import IngestionConflictError, IngestionNotFoundError
from edgebook.wagering.services import (
    WagerConflictError,
    WagerNotFoundError,
    WagerValidationError,
    correct_game_result,
    record_game_result,
)

router = APIRouter(prefix="/cfb", tags=["college-football"])

MILLIPOINT = Decimal("0.001")


def line_to_millipoints(value: Decimal) -> int:
    """Convert an exact three-decimal point line to integer millipoints."""
    try:
        line = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Line must be a decimal value") from error
    if not line.is_finite() or line != line.quantize(MILLIPOINT):
        raise ValueError("Line cannot have more than three decimal places")
    return int(line * 1000)


def millipoints_to_string(value: int | None) -> str | None:
    """Render an integer millipoint line as an exact decimal string."""
    if value is None:
        return None
    return f"{Decimal(value) / 1000:.3f}"


class TeamCreate(BaseModel):
    """Payload for a reusable college-football team."""

    name: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Team name cannot be blank")
        return value


class TeamResponse(BaseModel):
    """Public representation of a team catalog record."""

    id: str
    name: str
    created_at: str
    updated_at: str


class GameCreate(BaseModel):
    """Payload for manually creating a scheduled game."""

    home_team_id: str
    away_team_id: str
    scheduled_at: datetime
    sport: SportType = SportType.CFB

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Scheduled time must include a timezone")
        return value


class MarketCreate(BaseModel):
    """Payload for a game market; quotes are created as a separate resource."""

    market_type: MarketType
    line: Decimal | None = None

    @field_validator("line")
    @classmethod
    def validate_line_precision(cls, value: Decimal | None) -> Decimal | None:
        if value is not None:
            line_to_millipoints(value)
        return value


class QuoteCreate(BaseModel):
    """Payload for a manual American-odds quote."""

    selection: MarketSelection
    american_odds: int


class QuoteResponse(BaseModel):
    """Public representation of a market quote."""

    id: str
    selection: MarketSelection
    american_odds: int
    source: str | None
    source_quote_id: str | None
    observed_at: str | None
    created_at: str


class MarketResponse(BaseModel):
    """Public representation of a market and any entered quotes."""

    id: str
    market_type: MarketType
    line: str | None
    status: MarketStatus
    quotes: list[QuoteResponse]
    created_at: str
    updated_at: str


class GameResponse(BaseModel):
    """Public representation of a game including its manual market intake."""

    id: str
    sport: str
    home_team: TeamResponse
    away_team: TeamResponse
    scheduled_at: str
    status: str
    home_score: int | None
    away_score: int | None
    score_sync_state: ScoreSyncState
    markets: list[MarketResponse]
    created_at: str
    updated_at: str


def team_response(team: Team) -> TeamResponse:
    """Translate a team ORM model to its API response."""
    return TeamResponse(
        id=team.id,
        name=team.name,
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat(),
    )


def quote_response(quote: MarketQuote) -> QuoteResponse:
    """Translate an odds quote ORM model to its API response."""
    return QuoteResponse(
        id=quote.id,
        selection=MarketSelection(quote.selection),
        american_odds=quote.american_odds,
        source=quote.source,
        source_quote_id=quote.source_quote_id,
        observed_at=quote.observed_at.isoformat() if quote.observed_at else None,
        created_at=quote.created_at.isoformat(),
    )


def market_response(market: Market) -> MarketResponse:
    """Translate a market ORM model and its quotes to its API response."""
    return MarketResponse(
        id=market.id,
        market_type=MarketType(market.market_type),
        line=millipoints_to_string(market.line_millipoints),
        status=MarketStatus(market.status),
        quotes=[quote_response(quote) for quote in market.quotes],
        created_at=market.created_at.isoformat(),
        updated_at=market.updated_at.isoformat(),
    )


def game_response(game: Game) -> GameResponse:
    """Translate a fully-loaded game ORM model to its API response."""
    return GameResponse(
        id=game.id,
        sport=game.sport,
        home_team=team_response(game.home_team),
        away_team=team_response(game.away_team),
        scheduled_at=game.scheduled_at.isoformat(),
        status=game.status,
        home_score=game.home_score,
        away_score=game.away_score,
        score_sync_state=ScoreSyncState(game.score_sync_state),
        markets=[market_response(market) for market in game.markets],
        created_at=game.created_at.isoformat(),
        updated_at=game.updated_at.isoformat(),
    )


def raise_cfb_http_error(error: Exception) -> None:
    """Map expected CFB service errors to the documented HTTP contract."""
    if isinstance(error, CfbNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    if isinstance(error, CfbConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    if isinstance(error, CfbValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    if isinstance(error, WagerNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, WagerConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, WagerValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, IngestionNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, (IngestionConflictError,)):
        raise HTTPException(status_code=409, detail=str(error)) from error
    raise error


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team_endpoint(
    payload: TeamCreate, db: Session = Depends(get_db)
) -> TeamResponse:
    """Create a reusable manually-entered college-football team."""
    try:
        team = create_team(db, name=payload.name)
    except Exception as error:
        raise_cfb_http_error(error)
    return team_response(team)


@router.post("/games", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game_endpoint(
    payload: GameCreate, db: Session = Depends(get_db)
) -> GameResponse:
    """Create a scheduled game between two existing teams."""
    try:
        game = create_game(
            db,
            home_team_id=payload.home_team_id,
            away_team_id=payload.away_team_id,
            scheduled_at=payload.scheduled_at,
            sport=payload.sport,
        )
        game = get_game(db, game.id)
    except Exception as error:
        raise_cfb_http_error(error)
    return game_response(game)


@router.get("/games", response_model=list[GameResponse])
def list_games_endpoint(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[GameResponse]:
    """List games newest-first with optional status filter."""
    try:
        games, _ = list_games(db, status=status_filter, limit=limit, offset=offset)
    except Exception as error:
        raise_cfb_http_error(error)
    return [game_response(g) for g in games]


@router.get("/games/{game_id}", response_model=GameResponse)
def get_game_endpoint(game_id: str, db: Session = Depends(get_db)) -> GameResponse:
    """Retrieve a game with its manual markets and quotes."""
    try:
        game = get_game(db, game_id)
    except Exception as error:
        raise_cfb_http_error(error)
    return game_response(game)


@router.post(
    "/games/{game_id}/markets",
    response_model=MarketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_market_endpoint(
    game_id: str, payload: MarketCreate, db: Session = Depends(get_db)
) -> MarketResponse:
    """Create a draft spread, moneyline, or total market for a game."""
    try:
        market = create_market(
            db,
            game_id=game_id,
            market_type=payload.market_type,
            line_millipoints=(
                line_to_millipoints(payload.line) if payload.line is not None else None
            ),
        )
    except Exception as error:
        raise_cfb_http_error(error)
    return market_response(market)


@router.post(
    "/markets/{market_id}/quotes",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quote_endpoint(
    market_id: str, payload: QuoteCreate, db: Session = Depends(get_db)
) -> QuoteResponse:
    """Add a manual quote to a draft market."""
    try:
        quote = create_quote(
            db,
            market_id=market_id,
            selection=payload.selection,
            american_odds=payload.american_odds,
        )
    except Exception as error:
        raise_cfb_http_error(error)
    return quote_response(quote)


class QuoteComparisonResponse(BaseModel):
    market_id: str
    selection: MarketSelection
    best_quote_id: str
    worst_quote_id: str


class OddsHistoryResponse(BaseModel):
    """One immutable provider quote observation for charting line movement."""

    quote_id: str
    market_id: str
    market_type: MarketType
    selection: MarketSelection
    line: str | None
    american_odds: int
    source: str | None
    source_event_id: str | None
    observed_at: str | None


def odds_history_response(quote: MarketQuote) -> OddsHistoryResponse:
    """Render source-specific historical odds with its market context."""
    return OddsHistoryResponse(
        quote_id=quote.id,
        market_id=quote.market_id,
        market_type=MarketType(quote.market.market_type),
        selection=MarketSelection(quote.selection),
        line=millipoints_to_string(quote.market.line_millipoints),
        american_odds=quote.american_odds,
        source=quote.source,
        source_event_id=quote.source_event_id,
        observed_at=quote.observed_at.isoformat() if quote.observed_at else None,
    )


@router.get(
    "/games/{game_id}/quote-comparison", response_model=list[QuoteComparisonResponse]
)
def quote_comparison_endpoint(
    game_id: str, db: Session = Depends(get_db)
) -> list[QuoteComparisonResponse]:
    """Compare provider observations without selecting a canonical line."""
    try:
        rows = quote_comparison(db, game_id)
    except Exception as error:
        raise_cfb_http_error(error)
    return [QuoteComparisonResponse(**row) for row in rows]


@router.get("/games/{game_id}/odds-history", response_model=list[OddsHistoryResponse])
def odds_history_endpoint(
    game_id: str,
    source: str | None = Query(default=None, max_length=100),
    market_type: MarketType | None = Query(default=None),
    selection: MarketSelection | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[OddsHistoryResponse]:
    """Read chronological, bookmaker-specific pregame odds observations."""
    if start is not None and (start.tzinfo is None or start.utcoffset() is None):
        raise HTTPException(status_code=422, detail="start must include a timezone")
    if end is not None and (end.tzinfo is None or end.utcoffset() is None):
        raise HTTPException(status_code=422, detail="end must include a timezone")
    if start is not None and end is not None and start > end:
        raise HTTPException(status_code=422, detail="start cannot be after end")
    try:
        quotes = odds_history(
            db,
            game_id=game_id,
            source=source,
            market_type=market_type,
            selection=selection,
            start=start,
            end=end,
            limit=limit,
            offset=offset,
        )
    except Exception as error:
        raise_cfb_http_error(error)
    return [odds_history_response(quote) for quote in quotes]


class GameResultCreate(BaseModel):
    """A manually entered final score."""

    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


@router.put("/games/{game_id}/result", response_model=GameResponse)
def record_game_result_endpoint(
    game_id: str, payload: GameResultCreate, db: Session = Depends(get_db)
) -> GameResponse:
    """Finalize a game and settle its pending simulated bets atomically."""
    try:
        record_game_result(
            db,
            game_id=game_id,
            home_score=payload.home_score,
            away_score=payload.away_score,
        )
        game = get_game(db, game_id)
    except Exception as error:
        raise_cfb_http_error(error)
    return game_response(game)


class ScoreCorrectionCreate(BaseModel):
    """Payload for correcting a finalized game score."""

    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=1000)


class ScoreResolutionCreate(ScoreCorrectionCreate):
    """Local operator decision for a held provider-score conflict."""

    resolved_by: str = Field(min_length=1, max_length=200)


# TODO: Require admin-level authorization before exposing this local simulation
# endpoint outside a controlled environment.
@router.put("/games/{game_id}/correction", response_model=GameResponse)
def correct_game_result_endpoint(
    game_id: str, payload: ScoreCorrectionCreate, db: Session = Depends(get_db)
) -> GameResponse:
    """Correct a finalized score and re-settle all affected bets.

    Creates offsetting ledger entries to reverse prior payouts, re-settles
    bets with the corrected score, and records an audit-trail entry.
    """
    try:
        correct_game_result(
            db,
            game_id=game_id,
            home_score=payload.home_score,
            away_score=payload.away_score,
            reason=payload.reason,
        )
        game = get_game(db, game_id)
    except Exception as error:
        raise_cfb_http_error(error)
    return game_response(game)


@router.put("/games/{game_id}/resolve-score-conflict", response_model=GameResponse)
def resolve_score_conflict_endpoint(
    game_id: str, payload: ScoreResolutionCreate, db: Session = Depends(get_db)
) -> GameResponse:
    """Locally resolve held provider-score disagreement and settle atomically."""
    try:
        resolve_score_conflict(
            db,
            game_id=game_id,
            home_score=payload.home_score,
            away_score=payload.away_score,
            reason=payload.reason,
            resolved_by=payload.resolved_by,
        )
        game = get_game(db, game_id)
    except Exception as error:
        raise_cfb_http_error(error)
    return game_response(game)
