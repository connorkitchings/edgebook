"""Unit and integration coverage for generic double-entry ledger operations."""

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from edgebook.ledger.models import (
    Account,
    AccountKind,
    JournalEntry,
    Transaction,
    TransactionType,
)
from edgebook.ledger.services import (
    AccountConflictError,
    LedgerValidationError,
    _post_balanced_entry,
    create_account,
    record_manual_transaction,
)


def test_opening_bankroll_creates_balanced_postings(db_session):
    """A funded account inception creates equal and opposite immutable postings."""
    account = create_account(
        db_session, owner_name="Dana", starting_bankroll_cents=12_345
    )

    assert account.current_balance_cents == 12_345
    assert account.starting_bankroll_cents == 12_345
    postings = list(db_session.scalars(select(Transaction)))
    assert len(postings) == 2
    assert sum(posting.amount_cents for posting in postings) == 0
    assert {posting.transaction_type for posting in postings} == {
        TransactionType.DEPOSIT.value
    }

    capital_account = db_session.scalar(
        select(Account).where(Account.kind == AccountKind.EQUITY.value)
    )
    assert capital_account is not None
    assert capital_account.current_balance_cents == -12_345
    assert db_session.scalar(select(func.count()).select_from(JournalEntry)) == 1


def test_deposit_and_withdrawal_keep_ledger_balanced(db_session):
    """Manual cash actions update balances only alongside balanced postings."""
    account = create_account(
        db_session, owner_name="Dana", starting_bankroll_cents=1_000
    )

    deposit, account = record_manual_transaction(
        db_session,
        account_id=account.id,
        transaction_type=TransactionType.DEPOSIT,
        amount_cents=500,
        description="Practice credits",
    )
    withdrawal, account = record_manual_transaction(
        db_session,
        account_id=account.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount_cents=300,
        description="Rebalance",
    )

    assert deposit.amount_cents == 500
    assert withdrawal.amount_cents == -300
    assert account.current_balance_cents == 1_200
    assert db_session.scalar(select(func.sum(Transaction.amount_cents))) == 0
    assert db_session.scalar(select(func.count()).select_from(JournalEntry)) == 3


def test_withdrawal_cannot_overdraw_simulation_credits(db_session):
    """An attempted overdraft makes no new journal entry or balance change."""
    account = create_account(db_session, owner_name="Dana", starting_bankroll_cents=100)

    with pytest.raises(AccountConflictError, match="Insufficient"):
        record_manual_transaction(
            db_session,
            account_id=account.id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount_cents=101,
            description=None,
        )

    db_session.refresh(account)
    assert account.current_balance_cents == 100
    assert db_session.scalar(select(func.count()).select_from(JournalEntry)) == 1


def test_unbalanced_postings_are_rejected_before_balance_changes(db_session):
    """The posting primitive rejects non-double-entry journal events."""
    account = create_account(db_session, owner_name="Dana", starting_bankroll_cents=0)

    with pytest.raises(LedgerValidationError, match="balance"):
        _post_balanced_entry(
            db_session,
            transaction_type=TransactionType.ADJUSTMENT,
            description="Invalid",
            postings=[(account, 10), (account, -5)],
        )

    db_session.refresh(account)
    assert account.current_balance_cents == 0
    assert db_session.scalar(select(func.count()).select_from(JournalEntry)) == 0


def test_failed_account_creation_rolls_back_all_writes(db_session, monkeypatch):
    """A failure after account insertion rolls back the account and all ledger state."""

    def fail_posting(*args, **kwargs):
        raise RuntimeError("forced posting failure")

    monkeypatch.setattr("edgebook.ledger.services._post_balanced_entry", fail_posting)

    with pytest.raises(RuntimeError, match="forced"):
        create_account(db_session, owner_name="Dana", starting_bankroll_cents=100)

    assert db_session.scalar(select(func.count()).select_from(Account)) == 0
    assert db_session.scalar(select(func.count()).select_from(JournalEntry)) == 0
    assert db_session.scalar(select(func.count()).select_from(Transaction)) == 0


def test_ledger_rows_cannot_be_updated_or_deleted(db_session):
    """Database triggers enforce append-only journal and transaction history."""
    account = create_account(db_session, owner_name="Dana", starting_bankroll_cents=100)
    transaction = db_session.scalar(
        select(Transaction).where(Transaction.account_id == account.id)
    )
    journal_entry = db_session.get(JournalEntry, transaction.journal_entry_id)

    with pytest.raises(IntegrityError, match="immutable"):
        db_session.execute(
            text(
                "UPDATE ledger_transactions SET description = 'changed' WHERE id = :id"
            ),
            {"id": transaction.id},
        )
    db_session.rollback()

    with pytest.raises(IntegrityError, match="immutable"):
        db_session.execute(
            text("DELETE FROM ledger_journal_entries WHERE id = :id"),
            {"id": journal_entry.id},
        )
    db_session.rollback()
