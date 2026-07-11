"""FastAPI routes for account performance analytics."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from edgebook.analytics.services import (
    AnalyticsNotFoundError,
    compute_analytics,
)
from edgebook.core.database import get_db
from edgebook.core.money import cents_to_string

router = APIRouter(prefix="/accounts", tags=["analytics"])


class AnalyticsPeriod(BaseModel):
    from_: str | None = None
    to: str | None = None


class AnalyticsSummary(BaseModel):
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    total_staked: str
    total_payout: str
    net_profit: str
    roi: float
    sharpe_ratio: float | None
    current_balance: str
    max_drawdown: str
    max_drawdown_pct: float


class SportBreakdown(BaseModel):
    sport: str
    bets: int
    roi: float
    net_profit: str


class MarketTypeBreakdown(BaseModel):
    market_type: str
    bets: int
    roi: float
    net_profit: str


class RationaleBreakdown(BaseModel):
    category: str | None
    bets: int
    roi: float


class CalibrationBucket(BaseModel):
    bucket: str
    min_pct: int
    max_pct: int | None
    bets: int
    roi: float


class DrawdownPoint(BaseModel):
    timestamp: str
    balance: str
    peak: str
    drawdown_pct: float
    event: str


class BalancePoint(BaseModel):
    date: str
    balance: str


class AnalyticsResponse(BaseModel):
    account_id: str
    period: dict
    summary: AnalyticsSummary
    by_sport: list[SportBreakdown]
    by_market_type: list[MarketTypeBreakdown]
    by_rationale_category: list[RationaleBreakdown]
    allocation_calibration: list[CalibrationBucket]
    drawdown_series: list[DrawdownPoint]
    balance_series: list[BalancePoint]


def _format_summary(raw: dict) -> AnalyticsSummary:
    return AnalyticsSummary(
        total_bets=raw["total_bets"],
        wins=raw["wins"],
        losses=raw["losses"],
        pushes=raw["pushes"],
        win_rate=raw["win_rate"],
        total_staked=cents_to_string(raw["total_staked_cents"]),
        total_payout=cents_to_string(raw["total_payout_cents"]),
        net_profit=cents_to_string(raw["net_profit_cents"]),
        roi=raw["roi"],
        sharpe_ratio=raw["sharpe_ratio"],
        current_balance=cents_to_string(raw["current_balance_cents"]),
        max_drawdown=cents_to_string(raw["max_drawdown_cents"]),
        max_drawdown_pct=raw["max_drawdown_pct"],
    )


def _format_sport(rows: list[dict]) -> list[SportBreakdown]:
    return [
        SportBreakdown(
            sport=r["sport"],
            bets=r["bets"],
            roi=r["roi"],
            net_profit=cents_to_string(r["net_profit_cents"]),
        )
        for r in rows
    ]


def _format_market_type(rows: list[dict]) -> list[MarketTypeBreakdown]:
    return [
        MarketTypeBreakdown(
            market_type=r["market_type"],
            bets=r["bets"],
            roi=r["roi"],
            net_profit=cents_to_string(r["net_profit_cents"]),
        )
        for r in rows
    ]


def _format_rationale(rows: list[dict]) -> list[RationaleBreakdown]:
    return [
        RationaleBreakdown(category=r["category"], bets=r["bets"], roi=r["roi"])
        for r in rows
    ]


def _format_calibration(rows: list[dict]) -> list[CalibrationBucket]:
    return [
        CalibrationBucket(
            bucket=r["bucket"],
            min_pct=r["min_pct"],
            max_pct=r["max_pct"],
            bets=r["bets"],
            roi=r["roi"],
        )
        for r in rows
    ]


def _format_drawdown(rows: list[dict]) -> list[DrawdownPoint]:
    return [
        DrawdownPoint(
            timestamp=r["timestamp"],
            balance=cents_to_string(r["balance_cents"]),
            peak=cents_to_string(r["peak_cents"]),
            drawdown_pct=r["drawdown_pct"],
            event=r["event"],
        )
        for r in rows
    ]


def _format_balance(rows: list[dict]) -> list[BalancePoint]:
    return [
        BalancePoint(date=r["date"], balance=cents_to_string(r["balance_cents"]))
        for r in rows
    ]


@router.get("/{account_id}/analytics", response_model=AnalyticsResponse)
def get_analytics_endpoint(
    account_id: str,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    buckets: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    """Retrieve comprehensive performance analytics for a fictional account."""
    parsed_buckets: list[int] | None = None
    if buckets is not None:
        try:
            parsed_buckets = [int(b.strip()) for b in buckets.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="buckets must be a comma-separated list of integers",
            )

    try:
        raw = compute_analytics(
            db,
            account_id=account_id,
            from_dt=from_date,
            to_dt=to_date,
            buckets=parsed_buckets,
        )
    except AnalyticsNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return AnalyticsResponse(
        account_id=raw["account_id"],
        period=raw["period"],
        summary=_format_summary(raw["summary"]),
        by_sport=_format_sport(raw["by_sport"]),
        by_market_type=_format_market_type(raw["by_market_type"]),
        by_rationale_category=_format_rationale(raw["by_rationale_category"]),
        allocation_calibration=_format_calibration(raw["allocation_calibration"]),
        drawdown_series=_format_drawdown(raw["drawdown_series"]),
        balance_series=_format_balance(raw["balance_series"]),
    )
