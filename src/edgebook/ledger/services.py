"""Business operations for the generic double-entry simulation ledger."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from edgebook.ledger.models import (
    Account,
    AccountKind,
    JournalEntry,
    Transaction,
    TransactionType,
)

SYSTEM_CAPITAL_OWNER = "Edgebook Simulation Capital"


class LedgerError(Exception):
    """Base exception for expected ledger operation failures."""


class AccountNotFoundError(LedgerError):
    """Raised when a user-facing account cannot be found."""


class AccountConflictError(LedgerError):
    """Raised when an operation conflicts with account state."""


class LedgerValidationError(LedgerError):
    """Raised when a ledger invariant is violated."""


def _get_user_account(db: Session, account_id: str) -> Account:
    account = db.scalar(
        select(Account).where(
            Account.id == account_id,
            Account.kind == AccountKind.USER_ASSET.value,
        )
    )
    if account is None:
        raise AccountNotFoundError(f"Account {account_id} was not found")
    return account


def get_account(db: Session, account_id: str) -> Account:
    """Return a user-facing ledger account."""
    return _get_user_account(db, account_id)


def _get_or_create_capital_account(db: Session) -> Account:
    capital_account = db.scalar(
        select(Account).where(
            Account.owner_name == SYSTEM_CAPITAL_OWNER,
            Account.kind == AccountKind.EQUITY.value,
        )
    )
    if capital_account is None:
        capital_account = Account(
            owner_name=SYSTEM_CAPITAL_OWNER,
            kind=AccountKind.EQUITY.value,
            is_active=True,
            starting_bankroll_cents=0,
            current_balance_cents=0,
        )
        db.add(capital_account)
        db.flush()
    return capital_account


def _post_balanced_entry(
    db: Session,
    *,
    transaction_type: TransactionType,
    description: str,
    postings: Sequence[tuple[Account, int]],
) -> tuple[JournalEntry, list[Transaction]]:
    """Persist a balanced journal entry and synchronize each affected balance."""
    if len(postings) < 2:
        raise LedgerValidationError("A journal entry requires at least two postings")
    if any(amount == 0 for _, amount in postings):
        raise LedgerValidationError("Ledger postings must have non-zero amounts")
    if sum(amount for _, amount in postings) != 0:
        raise LedgerValidationError("Ledger postings must balance to zero")

    journal_entry = JournalEntry(description=description)
    db.add(journal_entry)
    db.flush()

    transactions: list[Transaction] = []
    for account, amount_cents in postings:
        transaction = Transaction(
            journal_entry_id=journal_entry.id,
            account_id=account.id,
            transaction_type=transaction_type.value,
            amount_cents=amount_cents,
            description=description,
        )
        account.current_balance_cents += amount_cents
        db.add(transaction)
        transactions.append(transaction)

    db.flush()
    return journal_entry, transactions


def create_account(
    db: Session, *, owner_name: str, starting_bankroll_cents: int
) -> Account:
    """Create a fictional account and, when funded, record its opening credit."""
    if starting_bankroll_cents < 0:
        raise LedgerValidationError("Starting bankroll cannot be negative")

    try:
        account = Account(
            owner_name=owner_name,
            kind=AccountKind.USER_ASSET.value,
            is_active=True,
            starting_bankroll_cents=starting_bankroll_cents,
            current_balance_cents=0,
        )
        db.add(account)
        db.flush()

        if starting_bankroll_cents:
            capital_account = _get_or_create_capital_account(db)
            _post_balanced_entry(
                db,
                transaction_type=TransactionType.DEPOSIT,
                description="Opening simulation-credit balance",
                postings=[
                    (account, starting_bankroll_cents),
                    (capital_account, -starting_bankroll_cents),
                ],
            )

        db.commit()
        db.refresh(account)
        return account
    except Exception:
        db.rollback()
        raise


def record_manual_transaction(
    db: Session,
    *,
    account_id: str,
    transaction_type: TransactionType,
    amount_cents: int,
    description: str | None,
) -> tuple[Transaction, Account]:
    """Record a fictional deposit or withdrawal using a balanced journal entry."""
    if transaction_type not in {TransactionType.DEPOSIT, TransactionType.WITHDRAWAL}:
        raise LedgerValidationError(
            "Only deposits and withdrawals are available manually"
        )
    if amount_cents <= 0:
        raise LedgerValidationError("Transaction amount must be positive")

    try:
        account = _get_user_account(db, account_id)
        if not account.is_active:
            raise AccountConflictError("Inactive accounts cannot accept transactions")
        if (
            transaction_type == TransactionType.WITHDRAWAL
            and account.current_balance_cents < amount_cents
        ):
            raise AccountConflictError("Insufficient simulation-credit balance")

        signed_amount = (
            amount_cents
            if transaction_type == TransactionType.DEPOSIT
            else -amount_cents
        )
        capital_account = _get_or_create_capital_account(db)
        _, transactions = _post_balanced_entry(
            db,
            transaction_type=transaction_type,
            description=description or transaction_type.value.replace("_", " ").title(),
            postings=[(account, signed_amount), (capital_account, -signed_amount)],
        )
        db.commit()
        db.refresh(account)
        return transactions[0], account
    except Exception:
        db.rollback()
        raise


def list_transactions(
    db: Session, *, account_id: str, limit: int, offset: int
) -> tuple[list[Transaction], int]:
    """Return a newest-first page of an account's ledger postings."""
    _get_user_account(db, account_id)
    statement = (
        select(Transaction)
        .where(Transaction.account_id == account_id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    total = db.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.account_id == account_id)
    )
    return list(db.scalars(statement)), int(total or 0)
