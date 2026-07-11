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
    ScoreCorrection,
)
from edgebook.ledger.models import TransactionType
from edgebook.ledger.services import (
    AccountConflictError,
    AccountNotFoundError,
    LedgerValidationError,
    get_account,
    post_adjustment,
    post_wager_transaction,
)
from edgebook.wagering.models import (
    Bet,
    BetReview,
    BetStatus,
    RationaleCategory,
    ReviewStatus,
)


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
    rationale_category: str | None = None,
    notes: str | None = None,
    quote_id: str | None = None,
    idempotency_key: str | None = None,
    now: datetime | None = None,
) -> tuple[Bet, int, bool]:
    """Atomically lock a quote, record a bet, and debit its fictional stake."""
    if stake_cents <= 0:
        raise WagerValidationError("Stake must be positive")
    if rationale_category is not None:
        try:
            RationaleCategory(rationale_category)
        except ValueError as error:
            raise WagerValidationError(
                f"Invalid rationale category: {rationale_category}"
            ) from error
    if idempotency_key:
        existing = db.scalar(
            select(Bet).where(
                Bet.account_id == account_id, Bet.idempotency_key == idempotency_key
            )
        )
        if existing is not None:
            normalized_reason = reason.strip() if reason else None
            normalized_notes = notes.strip() if notes else None
            if (
                existing.market_id != market_id
                or existing.selection != selection.value
                or existing.stake_cents != stake_cents
                or existing.reason != (normalized_reason or None)
                or existing.notes != (normalized_notes or None)
                or existing.rationale_category != rationale_category
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
    quote_query = select(MarketQuote).where(
        MarketQuote.market_id == market_id,
        MarketQuote.selection == selection.value,
    )
    if quote_id is not None:
        quote_query = quote_query.where(MarketQuote.id == quote_id)
    quotes = list(db.scalars(quote_query))
    quote = quotes[0] if len(quotes) == 1 else None
    if quote is None:
        if quote_id is None and len(quotes) > 1:
            raise WagerValidationError(
                "Multiple source quotes are available; quote_id is required"
            )
        raise WagerValidationError("Selection does not have the requested quote")

    normalized_reason = reason.strip() if reason else None
    normalized_notes = notes.strip() if notes else None
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
            quote_source=quote.source,
            quote_source_id=quote.source_quote_id,
            quote_observed_at=quote.observed_at,
            stake_cents=stake_cents,
            bankroll_before_cents=bankroll_before,
            reason=normalized_reason or None,
            rationale_category=rationale_category,
            notes=normalized_notes or None,
            status=BetStatus.PENDING.value,
        )
        db.add(bet)
        db.flush()
        db.add(
            BetReview(
                bet_id=bet.id,
                status=(
                    ReviewStatus.PENDING.value
                    if normalized_reason or normalized_notes or rationale_category
                    else ReviewStatus.NOT_APPLICABLE.value
                ),
            )
        )
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
    db: Session,
    *,
    game_id: str,
    home_score: int,
    away_score: int,
    commit: bool = True,
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
        if commit:
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


def correct_game_result(
    db: Session,
    *,
    game_id: str,
    home_score: int,
    away_score: int,
    reason: str,
) -> tuple[Game, list[Bet], ScoreCorrection]:
    """Correct a finalized score with a full audit trail.

    Reverses prior payout postings via offsetting ADJUSTMENT entries,
    resets all bets to PENDING, re-settles with corrected scores, and
    records a ScoreCorrection audit entry. The game remains FINAL.
    """
    if home_score < 0 or away_score < 0:
        raise WagerValidationError("Corrected scores must be non-negative")
    normalized_reason = reason.strip() if reason else None
    if not normalized_reason:
        raise WagerValidationError("A reason is required for score corrections")

    game = db.get(Game, game_id)
    if game is None:
        raise WagerNotFoundError(f"Game {game_id} was not found")
    if game.status != GameStatus.FINAL.value:
        raise WagerConflictError("Only finalized games can be corrected")
    if game.home_score == home_score and game.away_score == away_score:
        raise WagerValidationError("Corrected scores must differ from the original")

    original_home = int(game.home_score or 0)
    original_away = int(game.away_score or 0)

    try:
        bets = list(db.scalars(select(Bet).where(Bet.game_id == game_id)))

        for bet in bets:
            if bet.payout_cents and bet.payout_cents > 0:
                post_adjustment(
                    db,
                    account_id=bet.account_id,
                    amount_cents=-bet.payout_cents,
                    description=f"Score correction reversal for bet {bet.id}",
                )
            bet.status = BetStatus.PENDING.value
            bet.payout_cents = None
            bet.payout_transaction_id = None
            bet.settled_at = None

        game.home_score = home_score
        game.away_score = away_score

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
                    description=f"Corrected wager payout for bet {bet.id}",
                )
                bet.payout_transaction_id = payout_transaction.id
            bet.status = result.value
            bet.payout_cents = payout_cents
            bet.settled_at = settled_at

        correction = ScoreCorrection(
            game_id=game_id,
            original_home_score=original_home,
            original_away_score=original_away,
            corrected_home_score=home_score,
            corrected_away_score=away_score,
            reason=normalized_reason,
        )
        db.add(correction)

        db.commit()
        db.refresh(game)
        return game, bets, correction
    except Exception:
        db.rollback()
        raise


def list_bets(
    db: Session,
    *,
    account_id: str,
    limit: int,
    offset: int,
    status: str | None = None,
    market_type: str | None = None,
) -> tuple[list[Bet], int]:
    try:
        get_account(db, account_id)
    except (AccountNotFoundError, AccountConflictError, LedgerValidationError) as error:
        raise WagerNotFoundError(str(error)) from error
    conditions = [Bet.account_id == account_id]
    if status is not None:
        conditions.append(Bet.status == status)
    if market_type is not None:
        conditions.append(Bet.market_type == market_type)
    statement = (
        select(Bet)
        .where(*conditions)
        .order_by(Bet.placed_at.desc(), Bet.id.desc())
        .limit(limit)
        .offset(offset)
    )
    total = db.scalar(select(func.count()).select_from(Bet).where(*conditions))
    return list(db.scalars(statement)), int(total or 0)
