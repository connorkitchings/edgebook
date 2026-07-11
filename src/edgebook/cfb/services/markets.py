"""Manual college-football intake operations, markets and odds sub-module."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from edgebook.cfb.models import (
    Game,
    Market,
    MarketQuote,
    MarketSelection,
    MarketStatus,
    MarketType,
)
from edgebook.cfb.services.catalog import (
    CfbConflictError,
    CfbNotFoundError,
    CfbValidationError,
    get_game,
)

EXPECTED_SELECTIONS: dict[MarketType, set[MarketSelection]] = {
    MarketType.SPREAD: {MarketSelection.HOME, MarketSelection.AWAY},
    MarketType.MONEYLINE: {MarketSelection.HOME, MarketSelection.AWAY},
    MarketType.TOTAL: {MarketSelection.OVER, MarketSelection.UNDER},
}


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
