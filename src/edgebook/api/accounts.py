"""FastAPI routes for fictional accounts and generic ledger statements."""

from decimal import Decimal, InvalidOperation
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from edgebook.core.database import get_db
from edgebook.ledger.models import Account, Transaction, TransactionType
from edgebook.ledger.services import (
    AccountConflictError,
    AccountNotFoundError,
    LedgerValidationError,
    create_account,
    get_account,
    list_transactions,
    record_manual_transaction,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])

CENT = Decimal("0.01")


class ManualTransactionType(str, Enum):
    """Manual cash actions that are available before wagering is implemented."""

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


def validate_credit_amount(value: Decimal, *, allow_zero: bool = False) -> Decimal:
    """Validate a two-decimal simulation-credit amount without using floats."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Amount must be a decimal value") from error
    if not amount.is_finite():
        raise ValueError("Amount must be finite")
    if amount != amount.quantize(CENT):
        raise ValueError("Amount cannot have more than two decimal places")
    if amount < 0 or (amount == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"Amount must be {qualifier}")
    return amount


def decimal_to_cents(value: Decimal) -> int:
    """Convert a validated decimal simulation-credit amount to integer cents."""
    return int(value * 100)


def cents_to_string(value: int) -> str:
    """Render integer cents as an exact two-decimal string."""
    return f"{Decimal(value) / 100:.2f}"


class AccountCreate(BaseModel):
    """Payload for creating a fictional simulation-credit account."""

    owner_name: str = Field(min_length=1, max_length=200)
    starting_bankroll: Decimal = Decimal("0.00")

    @field_validator("owner_name")
    @classmethod
    def normalize_owner_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Owner name cannot be blank")
        return normalized

    @field_validator("starting_bankroll")
    @classmethod
    def validate_starting_bankroll(cls, value: Decimal) -> Decimal:
        return validate_credit_amount(value, allow_zero=True)


class AccountResponse(BaseModel):
    """Public representation of a fictional account."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_name: str
    is_active: bool
    starting_bankroll: str
    current_balance: str
    created_at: str
    updated_at: str


class TransactionCreate(BaseModel):
    """Payload for a manual deposit or withdrawal."""

    type: ManualTransactionType
    amount: Decimal
    description: str | None = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return validate_credit_amount(value)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class TransactionResponse(BaseModel):
    """Public representation of one signed account posting."""

    id: str
    journal_entry_id: str
    type: TransactionType
    amount: str
    description: str | None
    created_at: str


class TransactionPage(BaseModel):
    """A paginated account statement."""

    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int


class TransactionExecutionResponse(BaseModel):
    """The new account posting and balance returned after a manual action."""

    transaction: TransactionResponse
    current_balance: str


def account_response(account: Account) -> AccountResponse:
    """Translate storage-oriented account fields to the public API contract."""
    return AccountResponse(
        id=account.id,
        owner_name=account.owner_name,
        is_active=account.is_active,
        starting_bankroll=cents_to_string(account.starting_bankroll_cents),
        current_balance=cents_to_string(account.current_balance_cents),
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
    )


def transaction_response(transaction: Transaction) -> TransactionResponse:
    """Translate a storage-oriented ledger posting to the public API contract."""
    return TransactionResponse(
        id=transaction.id,
        journal_entry_id=transaction.journal_entry_id,
        type=TransactionType(transaction.transaction_type),
        amount=cents_to_string(transaction.amount_cents),
        description=transaction.description,
        created_at=transaction.created_at.isoformat(),
    )


def raise_ledger_http_error(error: Exception) -> None:
    """Map expected ledger service errors to the documented HTTP contract."""
    if isinstance(error, AccountNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    if isinstance(error, AccountConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    if isinstance(error, LedgerValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    raise error


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account_endpoint(
    payload: AccountCreate, db: Session = Depends(get_db)
) -> AccountResponse:
    """Create an active fictional account and optionally credit its opening bankroll."""
    try:
        account = create_account(
            db,
            owner_name=payload.owner_name,
            starting_bankroll_cents=decimal_to_cents(payload.starting_bankroll),
        )
    except Exception as error:
        raise_ledger_http_error(error)
    return account_response(account)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_endpoint(
    account_id: str, db: Session = Depends(get_db)
) -> AccountResponse:
    """Retrieve a fictional account's current balance and status."""
    try:
        account = get_account(db, account_id)
    except Exception as error:
        raise_ledger_http_error(error)
    return account_response(account)


@router.post(
    "/{account_id}/transactions",
    response_model=TransactionExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction_endpoint(
    account_id: str, payload: TransactionCreate, db: Session = Depends(get_db)
) -> TransactionExecutionResponse:
    """Execute one fictional deposit or withdrawal through the double-entry ledger."""
    try:
        transaction, account = record_manual_transaction(
            db,
            account_id=account_id,
            transaction_type=TransactionType(payload.type.value),
            amount_cents=decimal_to_cents(payload.amount),
            description=payload.description,
        )
    except Exception as error:
        raise_ledger_http_error(error)
    return TransactionExecutionResponse(
        transaction=transaction_response(transaction),
        current_balance=cents_to_string(account.current_balance_cents),
    )


@router.get("/{account_id}/transactions", response_model=TransactionPage)
def list_transactions_endpoint(
    account_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> TransactionPage:
    """List a newest-first paginated statement for one fictional account."""
    try:
        transactions, total = list_transactions(
            db, account_id=account_id, limit=limit, offset=offset
        )
    except Exception as error:
        raise_ledger_http_error(error)
    return TransactionPage(
        items=[transaction_response(transaction) for transaction in transactions],
        total=total,
        limit=limit,
        offset=offset,
    )
