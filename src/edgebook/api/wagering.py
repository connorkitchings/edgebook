"""FastAPI routes for simulated bet placement and history."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from edgebook.cfb.models import MarketSelection, MarketType
from edgebook.core.database import get_db
from edgebook.core.money import (
    cents_to_string,
    decimal_to_cents,
    validate_credit_amount,
)
from edgebook.ledger.services import AccountConflictError, AccountNotFoundError
from edgebook.wagering.models import Bet, BetStatus, RationaleCategory
from edgebook.wagering.services import (
    WagerConflictError,
    WagerNotFoundError,
    WagerValidationError,
    get_bet,
    list_bets,
    place_bet,
)

router = APIRouter(prefix="/accounts", tags=["simulated-wagers"])


class BetCreate(BaseModel):
    market_id: str
    selection: MarketSelection
    stake: Decimal
    reason: str | None = Field(default=None, max_length=500)
    rationale_category: RationaleCategory | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("stake")
    @classmethod
    def validate_stake(cls, value: Decimal) -> Decimal:
        return validate_credit_amount(value)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class BetResponse(BaseModel):
    id: str
    account_id: str
    game_id: str
    market_id: str
    quote_id: str
    stake_transaction_id: str
    payout_transaction_id: str | None
    selection: MarketSelection
    market_type: MarketType
    line: str | None
    american_odds: int
    stake: str
    bankroll_before: str
    payout: str | None
    reason: str | None
    rationale_category: str | None
    notes: str | None
    status: BetStatus
    placed_at: str
    settled_at: str | None


class BetPlacementResponse(BaseModel):
    bet: BetResponse
    current_balance: str


class BetPage(BaseModel):
    items: list[BetResponse]
    total: int
    limit: int
    offset: int


def bet_response(bet: Bet) -> BetResponse:
    line = (
        f"{Decimal(bet.line_millipoints) / 1000:.3f}"
        if bet.line_millipoints is not None
        else None
    )
    return BetResponse(
        id=bet.id,
        account_id=bet.account_id,
        game_id=bet.game_id,
        market_id=bet.market_id,
        quote_id=bet.quote_id,
        stake_transaction_id=bet.stake_transaction_id,
        payout_transaction_id=bet.payout_transaction_id,
        selection=MarketSelection(bet.selection),
        market_type=MarketType(bet.market_type),
        line=line,
        american_odds=bet.american_odds,
        stake=cents_to_string(bet.stake_cents),
        bankroll_before=cents_to_string(bet.bankroll_before_cents),
        payout=cents_to_string(bet.payout_cents)
        if bet.payout_cents is not None
        else None,
        reason=bet.reason,
        rationale_category=bet.rationale_category,
        notes=bet.notes,
        status=BetStatus(bet.status),
        placed_at=bet.placed_at.isoformat(),
        settled_at=bet.settled_at.isoformat() if bet.settled_at else None,
    )


def raise_wager_http_error(error: Exception) -> None:
    if isinstance(error, (WagerNotFoundError, AccountNotFoundError)):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, (WagerConflictError, AccountConflictError)):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, WagerValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    raise error


@router.post("/{account_id}/bets", response_model=BetPlacementResponse, status_code=201)
def place_bet_endpoint(
    account_id: str,
    payload: BetCreate,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, max_length=100),
) -> BetPlacementResponse:
    try:
        bet, current_balance, _ = place_bet(
            db,
            account_id=account_id,
            market_id=payload.market_id,
            selection=payload.selection,
            stake_cents=decimal_to_cents(payload.stake),
            reason=payload.reason,
            rationale_category=payload.rationale_category.value
            if payload.rationale_category
            else None,
            notes=payload.notes,
            idempotency_key=idempotency_key,
        )
    except Exception as error:
        raise_wager_http_error(error)
    return BetPlacementResponse(
        bet=bet_response(bet), current_balance=cents_to_string(current_balance)
    )


@router.get("/{account_id}/bets", response_model=BetPage)
def list_bets_endpoint(
    account_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> BetPage:
    try:
        bets, total = list_bets(db, account_id=account_id, limit=limit, offset=offset)
    except Exception as error:
        raise_wager_http_error(error)
    return BetPage(
        items=[bet_response(bet) for bet in bets],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{account_id}/bets/{bet_id}", response_model=BetResponse)
def get_bet_endpoint(
    account_id: str, bet_id: str, db: Session = Depends(get_db)
) -> BetResponse:
    try:
        bet = get_bet(db, account_id=account_id, bet_id=bet_id)
    except Exception as error:
        raise_wager_http_error(error)
    return bet_response(bet)
