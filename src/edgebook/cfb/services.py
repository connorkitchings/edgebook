"""Manual college-football intake operations, isolated from the ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from edgebook.cfb.models import (
    Game,
    GameStatus,
    Market,
    MarketQuote,
    MarketSelection,
    MarketStatus,
    MarketType,
    SportType,
    Team,
)


class CfbError(Exception):
    """Base exception for expected CFB domain operation failures."""


class CfbNotFoundError(CfbError):
    """Raised when a requested CFB resource cannot be found."""


class CfbConflictError(CfbError):
    """Raised when a CFB operation conflicts with stored state."""


class CfbValidationError(CfbError):
    """Raised when CFB domain validation fails."""


EXPECTED_SELECTIONS: dict[MarketType, set[MarketSelection]] = {
    MarketType.SPREAD: {MarketSelection.HOME, MarketSelection.AWAY},
    MarketType.MONEYLINE: {MarketSelection.HOME, MarketSelection.AWAY},
    MarketType.TOTAL: {MarketSelection.OVER, MarketSelection.UNDER},
}


def normalize_team_name(name: str) -> str:
    """Collapse whitespace and normalize a team name for uniqueness checks."""
    return " ".join(name.strip().split()).lower()


def create_team(db: Session, *, name: str) -> Team:
    """Create a reusable manually-entered team."""
    display_name = " ".join(name.strip().split())
    normalized_name = normalize_team_name(display_name)
    if (
        db.scalar(select(Team).where(Team.normalized_name == normalized_name))
        is not None
    ):
        raise CfbConflictError("A team with that name already exists")
    try:
        team = Team(name=display_name, normalized_name=normalized_name)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team
    except Exception:
        db.rollback()
        raise


def create_game(
    db: Session,
    *,
    home_team_id: str,
    away_team_id: str,
    scheduled_at: datetime,
    sport: SportType = SportType.CFB,
) -> Game:
    """Create a scheduled game after validating both teams."""
    if home_team_id == away_team_id:
        raise CfbValidationError("Home and away teams must be distinct")
    home_team = db.get(Team, home_team_id)
    away_team = db.get(Team, away_team_id)
    if home_team is None or away_team is None:
        raise CfbNotFoundError("Home and away teams must both exist")
    if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
        raise CfbValidationError("Scheduled time must include a timezone")
    try:
        game = Game(
            sport=sport,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            scheduled_at=scheduled_at.astimezone(UTC),
            status=GameStatus.SCHEDULED,
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        return game
    except Exception:
        db.rollback()
        raise


def get_game(db: Session, game_id: str) -> Game:
    """Return a game with the teams, markets, and quotes needed by its detail view."""
    game = db.scalar(
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
            selectinload(Game.markets).selectinload(Market.quotes),
        )
    )
    if game is None:
        raise CfbNotFoundError(f"Game {game_id} was not found")
    return game


def _validate_market_line(
    market_type: MarketType, line_millipoints: int | None
) -> None:
    if market_type == MarketType.MONEYLINE and line_millipoints is not None:
        raise CfbValidationError("Moneyline markets cannot have a point line")
    if market_type == MarketType.SPREAD and line_millipoints is None:
        raise CfbValidationError("Spread markets require a home-perspective line")
    if market_type == MarketType.TOTAL and (
        line_millipoints is None or line_millipoints < 0
    ):
        raise CfbValidationError("Total markets require a non-negative line")


def create_market(
    db: Session, *, game_id: str, market_type: MarketType, line_millipoints: int | None
) -> Market:
    """Create a draft market for a game.

    Multiple markets of the same type may coexist when they have different
    lines (alternate spreads/totals). Moneyline is limited to one per game.
    """
    if db.get(Game, game_id) is None:
        raise CfbNotFoundError(f"Game {game_id} was not found")
    _validate_market_line(market_type, line_millipoints)

    if market_type == MarketType.MONEYLINE:
        existing = db.scalar(
            select(Market).where(
                Market.game_id == game_id,
                Market.market_type == market_type,
            )
        )
        if existing is not None:
            raise CfbConflictError("This game already has a moneyline market")
    else:
        existing = db.scalar(
            select(Market).where(
                Market.game_id == game_id,
                Market.market_type == market_type,
                Market.line_millipoints == line_millipoints,
            )
        )
        if existing is not None:
            raise CfbConflictError(
                "This game already has that market type at the same line"
            )

    try:
        market = Market(
            game_id=game_id,
            market_type=market_type,
            line_millipoints=line_millipoints,
            status=MarketStatus.DRAFT,
        )
        db.add(market)
        db.commit()
        db.refresh(market)
        return market
    except Exception:
        db.rollback()
        raise


def create_quote(
    db: Session,
    *,
    market_id: str,
    selection: MarketSelection,
    american_odds: int,
    source: str | None = "MANUAL",
    source_quote_id: str | None = None,
) -> MarketQuote:
    """Add a manual quote and open the market when its quote pair is complete."""
    market = db.get(Market, market_id)
    if market is None:
        raise CfbNotFoundError(f"Market {market_id} was not found")
    market_type = MarketType(market.market_type)
    if selection not in EXPECTED_SELECTIONS[market_type]:
        raise CfbValidationError("Selection is not valid for this market type")
    if abs(american_odds) < 100:
        raise CfbValidationError("American odds must have a magnitude of at least 100")
    source_quote_id = source_quote_id or str(uuid4())
    if source == "MANUAL" and db.scalar(
        select(MarketQuote).where(
            MarketQuote.market_id == market_id,
            MarketQuote.selection == selection.value,
            MarketQuote.source == "MANUAL",
        )
    ):
        raise CfbConflictError("This market already has a quote for that selection")
    if db.scalar(
        select(MarketQuote).where(
            MarketQuote.market_id == market_id,
            MarketQuote.selection == selection.value,
            MarketQuote.source == source,
            MarketQuote.source_quote_id == source_quote_id,
        )
    ):
        raise CfbConflictError("This market already has a quote for that selection")
    try:
        quote = MarketQuote(
            market_id=market_id,
            selection=selection,
            american_odds=american_odds,
            source=source,
            source_quote_id=source_quote_id,
            observed_at=datetime.now(UTC),
        )
        db.add(quote)
        db.flush()
        selections = set(
            db.scalars(
                select(MarketQuote.selection).where(MarketQuote.market_id == market_id)
            )
        )
        if EXPECTED_SELECTIONS[market_type].issubset(
            {MarketSelection(selection_value) for selection_value in selections}
        ):
            market.status = MarketStatus.OPEN
        db.commit()
        db.refresh(quote)
        return quote
    except Exception:
        db.rollback()
        raise


def quote_comparison(db: Session, game_id: str) -> list[dict]:
    """Return derived best/worst source observations without canonicalizing odds."""
    game = get_game(db, game_id)
    rows: list[dict] = []
    for market in game.markets:
        for selection in EXPECTED_SELECTIONS[MarketType(market.market_type)]:
            quotes = [
                quote for quote in market.quotes if quote.selection == selection.value
            ]
            if not quotes:
                continue
            rows.append(
                {
                    "market_id": market.id,
                    "selection": selection.value,
                    "best_quote_id": max(
                        quotes, key=lambda quote: quote.american_odds
                    ).id,
                    "worst_quote_id": min(
                        quotes, key=lambda quote: quote.american_odds
                    ).id,
                }
            )
    return rows
