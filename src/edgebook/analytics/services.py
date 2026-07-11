"""Read-only analytics computation services for the Edgebook simulation platform.

All functions query existing data (bets, ledger transactions, games) and
return plain dicts suitable for Pydantic serialization. No data is modified.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from statistics import mean, pstdev

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from edgebook.cfb.models import Game
from edgebook.ledger.models import Account, Transaction
from edgebook.ledger.services import get_account
from edgebook.wagering.models import Bet, BetReview, BetStatus, ReviewStatus

DEFAULT_BUCKETS = [1, 2, 5, 10, 25]


class AnalyticsError(Exception):
    """Base exception for analytics operation failures."""


class AnalyticsNotFoundError(AnalyticsError):
    """Raised when the requested account cannot be found."""


def _validate_account(db: Session, account_id: str) -> Account:
    try:
        return get_account(db, account_id)
    except Exception as error:
        raise AnalyticsNotFoundError(str(error)) from error


def _settled_bet_filter(bet_cls, account_id: str, from_dt, to_dt):
    """Build a WHERE clause for settled bets within an optional date range."""
    conditions = [
        bet_cls.account_id == account_id,
        bet_cls.status.in_(
            [BetStatus.WON.value, BetStatus.LOST.value, BetStatus.PUSH.value]
        ),
    ]
    if from_dt is not None:
        conditions.append(bet_cls.settled_at >= from_dt)
    if to_dt is not None:
        conditions.append(bet_cls.settled_at <= to_dt)
    return conditions


def _opening_balance_cents(
    db: Session, account_id: str, from_dt: datetime | None
) -> int:
    """Return the balance immediately before an optional reporting period."""
    if from_dt is None:
        return 0
    opening_balance = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount_cents), 0)).where(
            Transaction.account_id == account_id,
            Transaction.created_at < from_dt,
        )
    )
    return int(opening_balance or 0)


def compute_summary(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> dict:
    """Compute headline performance metrics for an account."""
    account = _validate_account(db, account_id)

    conditions = _settled_bet_filter(Bet, account_id, from_dt, to_dt)
    bets = list(db.scalars(select(Bet).where(*conditions)))

    total_bets = len(bets)
    wins = sum(1 for b in bets if b.status == BetStatus.WON.value)
    losses = sum(1 for b in bets if b.status == BetStatus.LOST.value)
    pushes = sum(1 for b in bets if b.status == BetStatus.PUSH.value)
    total_staked = sum(b.stake_cents for b in bets)
    total_payout = sum(b.payout_cents or 0 for b in bets)
    net_profit = total_payout - total_staked
    roi = (net_profit / total_staked) if total_staked > 0 else 0.0
    win_rate = (wins / total_bets) if total_bets > 0 else 0.0

    per_bet_returns = [
        float((b.payout_cents or 0) - b.stake_cents) / b.stake_cents
        for b in bets
        if b.stake_cents > 0
    ]
    if len(per_bet_returns) >= 2:
        sharpe = mean(per_bet_returns) / pstdev(per_bet_returns)
    else:
        sharpe = None

    drawdown = compute_drawdown(db, account_id, from_dt, to_dt)
    max_dd_cents = drawdown["max_drawdown_cents"]
    max_dd_pct = drawdown["max_drawdown_pct"]

    return {
        "total_bets": total_bets,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": round(win_rate, 4),
        "total_staked_cents": total_staked,
        "total_payout_cents": total_payout,
        "net_profit_cents": net_profit,
        "roi": round(roi, 4),
        "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
        "current_balance_cents": account.current_balance_cents,
        "max_drawdown_cents": max_dd_cents,
        "max_drawdown_pct": round(max_dd_pct, 4),
    }


def compute_by_sport(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    """Group settled bet performance by sport."""
    conditions = _settled_bet_filter(Bet, account_id, from_dt, to_dt)
    rows = db.execute(
        select(
            Game.sport,
            func.count().label("bets"),
            func.coalesce(func.sum(Bet.stake_cents), 0).label("staked"),
            func.coalesce(func.sum(Bet.payout_cents), 0).label("payout"),
        )
        .join(Game, Bet.game_id == Game.id)
        .where(*conditions)
        .group_by(Game.sport)
        .order_by(Game.sport)
    ).all()

    results = []
    for sport, bets, staked, payout in rows:
        net = int(payout) - int(staked)
        roi = (net / int(staked)) if staked and int(staked) > 0 else 0.0
        results.append(
            {
                "sport": sport,
                "bets": int(bets),
                "roi": round(roi, 4),
                "net_profit_cents": net,
            }
        )
    return results


def compute_by_market_type(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    """Group settled bet performance by market type."""
    conditions = _settled_bet_filter(Bet, account_id, from_dt, to_dt)
    rows = db.execute(
        select(
            Bet.market_type,
            func.count().label("bets"),
            func.coalesce(func.sum(Bet.stake_cents), 0).label("staked"),
            func.coalesce(func.sum(Bet.payout_cents), 0).label("payout"),
        )
        .where(*conditions)
        .group_by(Bet.market_type)
        .order_by(Bet.market_type)
    ).all()

    results = []
    for market_type, bets, staked, payout in rows:
        net = int(payout) - int(staked)
        roi = (net / int(staked)) if staked and int(staked) > 0 else 0.0
        results.append(
            {
                "market_type": market_type,
                "bets": int(bets),
                "roi": round(roi, 4),
                "net_profit_cents": net,
            }
        )
    return results


def compute_by_rationale_category(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    """Group settled bet performance by rationale category."""
    conditions = _settled_bet_filter(Bet, account_id, from_dt, to_dt)
    rows = db.execute(
        select(
            Bet.rationale_category,
            func.count().label("bets"),
            func.coalesce(func.sum(Bet.stake_cents), 0).label("staked"),
            func.coalesce(func.sum(Bet.payout_cents), 0).label("payout"),
        )
        .where(*conditions)
        .group_by(Bet.rationale_category)
        .order_by(Bet.rationale_category)
    ).all()

    results = []
    for category, bets, staked, payout in rows:
        net = int(payout) - int(staked)
        roi = (net / int(staked)) if staked and int(staked) > 0 else 0.0
        results.append(
            {
                "category": category,
                "bets": int(bets),
                "roi": round(roi, 4),
            }
        )
    return results


def compute_allocation_calibration(
    db: Session,
    account_id: str,
    buckets: list[int] | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    """Bucket settled bets by conviction (stake / bankroll_before) and compute ROI."""
    if buckets is None:
        buckets = DEFAULT_BUCKETS

    conditions = _settled_bet_filter(Bet, account_id, from_dt, to_dt)
    bets = list(db.scalars(select(Bet).where(*conditions)))

    boundaries = [0] + sorted(buckets)
    results: list[dict] = []
    for i in range(len(boundaries)):
        lo = boundaries[i]
        if i < len(boundaries) - 1:
            hi = boundaries[i + 1]
            if lo == 0:
                label = f"<{hi}%"
            else:
                label = f"{lo}-{hi}%"
        else:
            hi = None
            label = f"{lo}%+"

        bucket_bets = []
        for b in bets:
            if b.bankroll_before_cents <= 0:
                continue
            pct = (b.stake_cents / b.bankroll_before_cents) * 100
            if hi is not None:
                if lo == 0:
                    in_bucket = pct < hi
                else:
                    in_bucket = lo <= pct < hi
            else:
                in_bucket = pct >= lo
            if in_bucket:
                bucket_bets.append(b)

        staked = sum(b.stake_cents for b in bucket_bets)
        payout = sum(b.payout_cents or 0 for b in bucket_bets)
        net = payout - staked
        roi = (net / staked) if staked > 0 else 0.0
        results.append(
            {
                "bucket": label,
                "min_pct": lo,
                "max_pct": hi,
                "bets": len(bucket_bets),
                "roi": round(roi, 4),
            }
        )
    return results


def compute_drawdown(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> dict:
    """Compute max drawdown by replaying the account's ledger chronologically."""
    _validate_account(db, account_id)

    tx_conditions = [Transaction.account_id == account_id]
    if from_dt is not None:
        tx_conditions.append(Transaction.created_at >= from_dt)
    if to_dt is not None:
        tx_conditions.append(Transaction.created_at <= to_dt)

    transactions = list(
        db.scalars(
            select(Transaction)
            .where(*tx_conditions)
            .order_by(Transaction.created_at.asc(), Transaction.id.asc())
        )
    )

    balance = _opening_balance_cents(db, account_id, from_dt)
    peak = balance
    max_dd_cents = 0
    max_dd_pct = 0.0

    for tx in transactions:
        balance += tx.amount_cents
        if balance > peak:
            peak = balance
        dd_cents = balance - peak
        dd_pct = (dd_cents / peak) if peak > 0 else 0.0
        if dd_cents < max_dd_cents:
            max_dd_cents = dd_cents
            max_dd_pct = dd_pct

    return {
        "max_drawdown_cents": max_dd_cents,
        "max_drawdown_pct": abs(max_dd_pct) if max_dd_pct < 0 else 0.0,
    }


def compute_drawdown_series(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    """Emit per-transaction drawdown points for chart rendering."""
    _validate_account(db, account_id)

    tx_conditions = [Transaction.account_id == account_id]
    if from_dt is not None:
        tx_conditions.append(Transaction.created_at >= from_dt)
    if to_dt is not None:
        tx_conditions.append(Transaction.created_at <= to_dt)

    transactions = list(
        db.scalars(
            select(Transaction)
            .where(*tx_conditions)
            .order_by(Transaction.created_at.asc(), Transaction.id.asc())
        )
    )

    balance = _opening_balance_cents(db, account_id, from_dt)
    peak = balance
    series: list[dict] = []

    if from_dt is not None:
        series.append(
            {
                "timestamp": from_dt.isoformat(),
                "balance_cents": balance,
                "peak_cents": peak,
                "drawdown_pct": 0.0,
                "event": "OPENING_BALANCE",
            }
        )

    for tx in transactions:
        balance += tx.amount_cents
        if balance > peak:
            peak = balance
        dd_pct = ((balance - peak) / peak * 100) if peak > 0 else 0.0
        series.append(
            {
                "timestamp": tx.created_at.isoformat(),
                "balance_cents": balance,
                "peak_cents": peak,
                "drawdown_pct": round(dd_pct, 2),
                "event": tx.transaction_type,
            }
        )
    return series


def compute_balance_series(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[dict]:
    """Emit daily balance points for chart rendering."""
    _validate_account(db, account_id)

    tx_conditions = [Transaction.account_id == account_id]
    if from_dt is not None:
        tx_conditions.append(Transaction.created_at >= from_dt)
    if to_dt is not None:
        tx_conditions.append(Transaction.created_at <= to_dt)

    transactions = list(
        db.scalars(
            select(Transaction)
            .where(*tx_conditions)
            .order_by(Transaction.created_at.asc(), Transaction.id.asc())
        )
    )

    opening_balance = _opening_balance_cents(db, account_id, from_dt)

    if not transactions:
        return [
            {
                "date": (
                    from_dt.date().isoformat()
                    if from_dt is not None
                    else datetime.now(UTC).date().isoformat()
                ),
                "balance_cents": opening_balance,
            }
        ]

    daily: dict[str, int] = {}
    balance = opening_balance

    first_date = (
        from_dt.date() if from_dt is not None else transactions[0].created_at.date()
    )
    daily[first_date.isoformat()] = balance

    for tx in transactions:
        balance += tx.amount_cents
        day_key = tx.created_at.date().isoformat()
        daily[day_key] = balance

    return [
        {"date": date_str, "balance_cents": bal}
        for date_str, bal in sorted(daily.items())
    ]


def compute_review_summary(db: Session, account_id: str) -> dict:
    """Summarize non-financial human-review workflow coverage and bias tags."""
    rows = db.execute(
        select(BetReview.status, BetReview.bias_flags)
        .join(Bet, BetReview.bet_id == Bet.id)
        .where(Bet.account_id == account_id)
    ).all()
    counts = {status.value: 0 for status in ReviewStatus}
    flags: dict[str, int] = {}
    for status, raw_flags in rows:
        counts[status] = counts.get(status, 0) + 1
        for flag in json.loads(raw_flags or "[]"):
            flags[flag] = flags.get(flag, 0) + 1
    eligible = len(rows) - counts[ReviewStatus.NOT_APPLICABLE.value]
    completed = counts[ReviewStatus.COMPLETED.value]
    return {
        "eligible": eligible,
        "completed": completed,
        "coverage": round(completed / eligible, 4) if eligible else 0.0,
        "status_counts": counts,
        "bias_flags": [
            {"flag": flag, "count": count} for flag, count in sorted(flags.items())
        ],
    }


def compute_analytics(
    db: Session,
    account_id: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    buckets: list[int] | None = None,
) -> dict:
    """Orchestrate all analytics computations into a single response."""
    return {
        "account_id": account_id,
        "period": {
            "from": from_dt.isoformat() if from_dt else None,
            "to": to_dt.isoformat() if to_dt else None,
        },
        "summary": compute_summary(db, account_id, from_dt, to_dt),
        "by_sport": compute_by_sport(db, account_id, from_dt, to_dt),
        "by_market_type": compute_by_market_type(db, account_id, from_dt, to_dt),
        "by_rationale_category": compute_by_rationale_category(
            db, account_id, from_dt, to_dt
        ),
        "allocation_calibration": compute_allocation_calibration(
            db, account_id, buckets, from_dt, to_dt
        ),
        "drawdown_series": compute_drawdown_series(db, account_id, from_dt, to_dt),
        "balance_series": compute_balance_series(db, account_id, from_dt, to_dt),
        "review_summary": compute_review_summary(db, account_id),
    }
