"""Atomic placement, settlement, and history operations for simulated wagers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from edgebook.cfb.models import (
    Game,
    GameStatus,
    Market,
    MarketQuote,
    MarketSelection,
    MarketStatus,
    MarketType,
)
from edgebook.ledger.models import TransactionType
from edgebook.ledger.services import (
    AccountConflictError,
    AccountNotFoundError,
    LedgerValidationError,
    get_account,
    post_wager_transaction,
)
from edgebook.wagering.models import Bet, BetStatus


class WageringError(Exception):
    """Base exception for expected wager lifecycle failures."""


class WagerNotFoundError(WageringError):
    pass


class WagerConflictError(WageringError):
    pass


class WagerValidationError(WageringError):
    pass


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def place_bet(
    db: Session,
    *,
    account_id: str,
    market_id: str,
    selection: MarketSelection,
    stake_cents: int,
    reason: str | None,
    idempotency_key: str | None = None,
    now: datetime | None = None,
) -> tuple[Bet, int, bool]:
    """Atomically lock a quote, record a bet, and debit its fictional stake."""
    if stake_cents <= 0:
        raise WagerValidationError("Stake must be positive")
    if idempotency_key:
        existing = db.scalar(
            select(Bet).where(
                Bet.account_id == account_id, Bet.idempotency_key == idempotency_key
            )
        )
        if existing is not None:
            normalized_reason = reason.strip() if reason else None
            if (
                existing.market_id != market_id
                or existing.selection != selection.value
                or existing.stake_cents != stake_cents
                or existing.reason != (normalized_reason or None)
            ):
                raise WagerConflictError(
                    "Idempotency key was already used for a different bet"
                )
            account = get_account(db, account_id)
            return existing, account.current_balance_cents, False

    market = db.get(Market, market_id)
    if market is None:
        raise WagerNotFoundError(f"Market {market_id} was not found")
    game = db.get(Game, market.game_id)
    if game is None:
        raise WagerNotFoundError(f"Game {market.game_id} was not found")
    if market.status != MarketStatus.OPEN.value:
        raise WagerConflictError("Only open markets accept bets")
    cutoff = _as_utc(game.scheduled_at) - timedelta(minutes=30)
    if _as_utc(now or datetime.now(UTC)) >= cutoff:
        raise WagerConflictError("Betting closes 30 minutes before scheduled kickoff")
    quote = db.scalar(
        select(MarketQuote).where(
            MarketQuote.market_id == market_id,
            MarketQuote.selection == selection.value,
        )
    )
    if quote is None:
        raise WagerValidationError("Selection does not have a quote in this market")

    normalized_reason = reason.strip() if reason else None
    try:
        account = get_account(db, account_id)
        bankroll_before = account.current_balance_cents
        stake_transaction, account = post_wager_transaction(
            db,
            account_id=account_id,
            transaction_type=TransactionType.WAGER_STAKE,
            amount_cents=stake_cents,
            description=f"Simulated wager stake on market {market.id}",
        )
        bet = Bet(
            account_id=account_id,
            game_id=game.id,
            market_id=market.id,
            quote_id=quote.id,
            stake_transaction_id=stake_transaction.id,
            idempotency_key=idempotency_key,
            selection=selection.value,
            market_type=market.market_type,
            line_millipoints=market.line_millipoints,
            american_odds=quote.american_odds,
            stake_cents=stake_cents,
            bankroll_before_cents=bankroll_before,
            reason=normalized_reason or None,
            status=BetStatus.PENDING.value,
        )
        db.add(bet)
        db.commit()
        db.refresh(bet)
        return bet, account.current_balance_cents, True
    except Exception:
        db.rollback()
        raise


def _result_for_bet(bet: Bet, home_score: int, away_score: int) -> BetStatus:
    selection = MarketSelection(bet.selection)
    market_type = MarketType(bet.market_type)
    comparison: int
    if market_type == MarketType.MONEYLINE:
        comparison = home_score - away_score
    elif market_type == MarketType.SPREAD:
        comparison = (home_score - away_score) * 1000 + int(bet.line_millipoints or 0)
    else:
        comparison = (home_score + away_score) * 1000 - int(bet.line_millipoints or 0)

    if comparison == 0:
        return BetStatus.PUSH
    selected_positive = selection in {MarketSelection.HOME, MarketSelection.OVER}
    return BetStatus.WON if (comparison > 0) == selected_positive else BetStatus.LOST


def _winning_payout_cents(stake_cents: int, american_odds: int) -> int:
    stake = Decimal(stake_cents)
    if american_odds > 0:
        profit = stake * Decimal(american_odds) / Decimal(100)
    else:
        profit = stake * Decimal(100) / Decimal(abs(american_odds))
    return stake_cents + int(profit.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def record_game_result(
    db: Session, *, game_id: str, home_score: int, away_score: int
) -> tuple[Game, list[Bet]]:
    """Finalize a score and atomically settle every pending bet for the game."""
    if home_score < 0 or away_score < 0:
        raise WagerValidationError("Final scores must be non-negative")
    game = db.get(Game, game_id)
    if game is None:
        raise WagerNotFoundError(f"Game {game_id} was not found")
    if game.status == GameStatus.FINAL.value:
        if game.home_score == home_score and game.away_score == away_score:
            bets = list(db.scalars(select(Bet).where(Bet.game_id == game_id)))
            return game, bets
        raise WagerConflictError(
            "A finalized game cannot be assigned a different score"
        )

    try:
        bets = list(
            db.scalars(
                select(Bet).where(
                    Bet.game_id == game_id, Bet.status == BetStatus.PENDING.value
                )
            )
        )
        settled_at = datetime.now(UTC)
        for bet in bets:
            result = _result_for_bet(bet, home_score, away_score)
            payout_cents = 0
            if result == BetStatus.PUSH:
                payout_cents = bet.stake_cents
            elif result == BetStatus.WON:
                payout_cents = _winning_payout_cents(bet.stake_cents, bet.american_odds)
            if payout_cents:
                payout_transaction, _ = post_wager_transaction(
                    db,
                    account_id=bet.account_id,
                    transaction_type=TransactionType.WAGER_PAYOUT,
                    amount_cents=payout_cents,
                    description=f"Simulated wager payout for bet {bet.id}",
                )
                bet.payout_transaction_id = payout_transaction.id
            bet.status = result.value
            bet.payout_cents = payout_cents
            bet.settled_at = settled_at

        game.status = GameStatus.FINAL
        game.home_score = home_score
        game.away_score = away_score
        db.commit()
        db.refresh(game)
        return game, bets
    except Exception:
        db.rollback()
        raise


def get_bet(db: Session, *, account_id: str, bet_id: str) -> Bet:
    try:
        get_account(db, account_id)
    except (AccountNotFoundError, AccountConflictError, LedgerValidationError) as error:
        raise WagerNotFoundError(str(error)) from error
    bet = db.scalar(select(Bet).where(Bet.id == bet_id, Bet.account_id == account_id))
    if bet is None:
        raise WagerNotFoundError(f"Bet {bet_id} was not found")
    return bet


def list_bets(
    db: Session, *, account_id: str, limit: int, offset: int
) -> tuple[list[Bet], int]:
    try:
        get_account(db, account_id)
    except (AccountNotFoundError, AccountConflictError, LedgerValidationError) as error:
        raise WagerNotFoundError(str(error)) from error
    statement = (
        select(Bet)
        .where(Bet.account_id == account_id)
        .order_by(Bet.placed_at.desc(), Bet.id.desc())
        .limit(limit)
        .offset(offset)
    )
    total = db.scalar(
        select(func.count()).select_from(Bet).where(Bet.account_id == account_id)
    )
    return list(db.scalars(statement)), int(total or 0)
