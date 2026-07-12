"""Server-rendered page routes for the Edgebook UI."""

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from edgebook.api.accounts import account_response
from edgebook.api.cfb import game_response
from edgebook.api.wagering import BetResponse, bet_response
from edgebook.cfb.models import Game, Market, MarketQuote, MarketSelection, Team
from edgebook.cfb.services import create_game, create_team, get_game, list_games
from edgebook.core.database import get_db
from edgebook.core.money import decimal_to_cents, validate_credit_amount
from edgebook.core.templates import templates
from edgebook.wagering.models import RationaleCategory
from edgebook.wagering.services import list_bets, place_bet, record_game_result

router = APIRouter(tags=["pages"])

RATIONALE_CATEGORIES = list(RationaleCategory)


def _get_first_account(db: Session):
    try:
        from edgebook.ledger.models import Account

        return db.query(Account).filter(Account.is_active.is_(True)).first()
    except Exception:
        return None


@router.get("/", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
):
    account = _get_first_account(db)
    balance_series = []

    if account:
        try:
            from edgebook.analytics.services import compute_analytics

            raw = compute_analytics(db, account_id=account.id)
            balance_series = [
                {"date": p["date"], "balance": f"{int(p['balance_cents']) / 100:.2f}"}
                for p in raw.get("balance_series", [])
            ]
        except Exception:
            balance_series = []

    context: dict[str, object] = {
        "active_page": "dashboard",
        "account": account_response(account) if account else None,
        "balance_series": balance_series,
    }
    if account:
        context["net_pnl_cents"] = (
            account.current_balance_cents - account.starting_bankroll_cents
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        context,
    )


@router.get("/bets", response_class=HTMLResponse)
def bets_page(
    request: Request,
    db: Session = Depends(get_db),
):
    account = _get_first_account(db)
    return templates.TemplateResponse(
        request,
        "bets.html",
        {
            "active_page": "bets",
            "account": account_response(account) if account else None,
        },
    )


@router.get("/bets/history", response_class=HTMLResponse)
def bet_history_page(
    request: Request,
    db: Session = Depends(get_db),
):
    account = _get_first_account(db)
    return templates.TemplateResponse(
        request,
        "bets/history.html",
        {
            "active_page": "bets",
            "account": account_response(account) if account else None,
        },
    )


@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(
    request: Request,
    db: Session = Depends(get_db),
):
    account = _get_first_account(db)
    context: dict[str, object] = {
        "active_page": "analytics",
        "account": account_response(account) if account else None,
        "summary": None,
    }

    if account:
        try:
            from edgebook.analytics.services import compute_analytics

            raw = compute_analytics(db, account_id=account.id)
            summary = raw["summary"]
            context["summary"] = summary

            balance_series = raw.get("balance_series", [])
            context["balance_dates"] = [p["date"] for p in balance_series]
            context["balance_values"] = [
                int(p["balance_cents"]) / 100 for p in balance_series
            ]

            drawdown_series = raw.get("drawdown_series", [])
            context["drawdown_labels"] = [p["timestamp"][:10] for p in drawdown_series]
            context["drawdown_values"] = [
                round(p["drawdown_pct"] * 100, 2) for p in drawdown_series
            ]

            by_market = raw.get("by_market_type", [])
            context["market_labels"] = [r["market_type"] for r in by_market]
            context["market_values"] = [round(r["roi"] * 100, 2) for r in by_market]
            context["market_colors"] = [
                "#22c55e" if r["roi"] >= 0 else "#ef4444" for r in by_market
            ]

            context["calibration"] = raw.get("allocation_calibration", [])
            context["review_summary"] = raw.get(
                "review_summary",
                {
                    "eligible": 0,
                    "completed": 0,
                    "coverage": 0.0,
                    "bias_flags": [],
                },
            )
        except Exception:
            pass

    return templates.TemplateResponse(
        request,
        "analytics.html",
        context,
    )


@router.get("/ingestion", response_class=HTMLResponse)
def ingestion_page(
    request: Request,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request,
        "ingestion.html",
        {"active_page": "ingestion"},
    )


# --- HTMX Partials: Dashboard ---


@router.get("/partials/recent-bets", response_class=HTMLResponse)
def recent_bets_partial(
    request: Request,
    account_id: str | None = None,
    db: Session = Depends(get_db),
):
    bets: list[BetResponse] = []
    matchups: dict[str, str] = {}
    if account_id:
        try:
            bets_list, _ = list_bets(db, account_id=account_id, limit=5, offset=0)
            bets = [bet_response(b) for b in bets_list]
            game_ids = {b.game_id for b in bets_list}
            if game_ids:
                games = db.query(Game).filter(Game.id.in_(game_ids)).all()
                matchups = {
                    g.id: f"{g.home_team.name} vs {g.away_team.name}" for g in games
                }
        except Exception:
            bets = []
            matchups = {}

    return templates.TemplateResponse(
        request,
        "partials/recent_bets.html",
        {"bets": bets, "matchups": matchups},
    )


# --- HTMX Partials: Bet History ---


_BET_STATUSES = [
    ("PENDING", "Pending"),
    ("WON", "Won"),
    ("LOST", "Lost"),
    ("PUSH", "Push"),
]
_MARKET_TYPES = ["SPREAD", "MONEYLINE", "TOTAL"]


@router.get("/partials/bet-table", response_class=HTMLResponse)
def bet_table_partial(
    request: Request,
    account_id: str,
    status: str | None = None,
    market_type: str | None = None,
    offset: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
):
    page_size = min(max(limit, 1), 100)
    bets_list, total = list_bets(
        db,
        account_id=account_id,
        limit=page_size,
        offset=offset,
        status=status,
        market_type=market_type,
    )
    bets = [bet_response(b) for b in bets_list]
    has_more = offset + page_size < total
    next_offset = offset + page_size
    return templates.TemplateResponse(
        request,
        "partials/bet_table.html",
        {
            "bets": bets,
            "account_id": account_id,
            "current_status": status,
            "current_market_type": market_type,
            "statuses": _BET_STATUSES,
            "market_types": _MARKET_TYPES,
            "has_more": has_more,
            "next_offset": next_offset,
        },
    )


# --- HTMX Partials: Bet Placement Wizard ---


@router.get("/partials/game-select", response_class=HTMLResponse)
def game_select_partial(
    request: Request,
    db: Session = Depends(get_db),
):
    games, _ = list_games(db, limit=50, offset=0)
    game_responses = [game_response(g) for g in games]
    return templates.TemplateResponse(
        request,
        "partials/game_select.html",
        {"games": game_responses},
    )


@router.get("/partials/market-picker", response_class=HTMLResponse)
def market_picker_partial(
    request: Request,
    game_id: str,
    db: Session = Depends(get_db),
):
    game = get_game(db, game_id)
    return templates.TemplateResponse(
        request,
        "partials/market_picker.html",
        {"game": game_response(game)},
    )


@router.get("/partials/stake-form", response_class=HTMLResponse)
def stake_form_partial(
    request: Request,
    market_id: str,
    selection: str,
    quote_id: str,
    account_id: str,
    db: Session = Depends(get_db),
):
    from edgebook.cfb.models import Market, MarketQuote

    market = db.get(Market, market_id)
    if market is None:
        return templates.TemplateResponse(
            request,
            "partials/game_select.html",
            {"games": []},
        )
    quote = db.get(MarketQuote, quote_id)
    game = get_game(db, market.game_id)
    line = (
        f"{Decimal(market.line_millipoints) / 1000:.3f}"
        if market.line_millipoints is not None
        else None
    )
    return templates.TemplateResponse(
        request,
        "partials/stake_form.html",
        {
            "market_id": market_id,
            "selection": selection,
            "quote_id": quote_id,
            "account_id": account_id,
            "american_odds": quote.american_odds if quote else 0,
            "market_type": market.market_type,
            "line": line,
            "game_id": game.id,
            "rationale_categories": RATIONALE_CATEGORIES,
        },
    )


@router.post("/partials/place-bet", response_class=HTMLResponse)
def place_bet_partial(
    request: Request,
    account_id: str = Form(...),
    market_id: str = Form(...),
    selection: str = Form(...),
    quote_id: str = Form(...),
    stake: str = Form(...),
    rationale_category: str = Form(""),
    reason: str = Form(""),
    db: Session = Depends(get_db),
):
    market = db.get(Market, market_id)
    if market is None:
        return templates.TemplateResponse(
            request,
            "partials/game_select.html",
            {"games": []},
        )

    game_id = market.game_id
    line = (
        f"{Decimal(market.line_millipoints) / 1000:.3f}"
        if market.line_millipoints is not None
        else None
    )

    try:
        stake_decimal = Decimal(stake)
        validate_credit_amount(stake_decimal)
        stake_cents = decimal_to_cents(stake_decimal)
    except (InvalidOperation, ValueError) as error:
        return templates.TemplateResponse(
            request,
            "partials/stake_form_error.html",
            {
                "error": f"Invalid stake amount: {error}",
                "market_id": market_id,
                "selection": selection,
                "quote_id": quote_id,
                "account_id": account_id,
                "american_odds": 0,
                "market_type": market.market_type,
                "line": line,
                "game_id": game_id,
                "rationale_categories": RATIONALE_CATEGORIES,
            },
        )

    try:
        bet, current_balance, _ = place_bet(
            db,
            account_id=account_id,
            market_id=market_id,
            selection=MarketSelection(selection),
            stake_cents=stake_cents,
            reason=reason.strip() or None,
            rationale_category=rationale_category or None,
            quote_id=quote_id,
        )
    except Exception as error:
        quote = db.get(MarketQuote, quote_id)
        return templates.TemplateResponse(
            request,
            "partials/stake_form_error.html",
            {
                "error": str(error),
                "market_id": market_id,
                "selection": selection,
                "quote_id": quote_id,
                "account_id": account_id,
                "american_odds": quote.american_odds if quote else 0,
                "market_type": market.market_type,
                "line": line,
                "game_id": game_id,
                "rationale_categories": RATIONALE_CATEGORIES,
                "stake_value": stake,
                "reason": reason,
                "rationale_category": rationale_category,
            },
        )

    return templates.TemplateResponse(
        request,
        "partials/bet_confirmation.html",
        {
            "bet": bet_response(bet),
            "current_balance": f"{current_balance / 100:.2f}",
        },
    )


# --- HTMX Partials: Game Management ---


@router.get("/games", response_class=HTMLResponse)
def games_page(
    request: Request,
    db: Session = Depends(get_db),
):
    teams = db.query(Team).order_by(Team.name).all()
    return templates.TemplateResponse(
        request,
        "games.html",
        {
            "active_page": "games",
            "teams": teams,
        },
    )


@router.get("/partials/game-list", response_class=HTMLResponse)
def game_list_partial(
    request: Request,
    db: Session = Depends(get_db),
):
    games, _ = list_games(db, limit=50, offset=0)
    game_responses = [game_response(g) for g in games]
    return templates.TemplateResponse(
        request,
        "partials/game_list.html",
        {"games": game_responses},
    )


@router.post("/partials/create-team", response_class=HTMLResponse)
def create_team_partial(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        team = create_team(db, name=name)
        return templates.TemplateResponse(
            request,
            "partials/_simple_message.html",
            {"message": f"Created: {team.name}", "level": "success"},
        )
    except Exception as error:
        return templates.TemplateResponse(
            request,
            "partials/_simple_message.html",
            {"message": str(error), "level": "error"},
        )


@router.post("/partials/create-game", response_class=HTMLResponse)
def create_game_partial(
    request: Request,
    home_team_id: str = Form(...),
    away_team_id: str = Form(...),
    scheduled_at: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        dt = datetime.fromisoformat(scheduled_at).replace(tzinfo=UTC)
        game = create_game(
            db,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            scheduled_at=dt,
        )
        return templates.TemplateResponse(
            request,
            "partials/_simple_message.html",
            {"message": f"Game created: {game.id}", "level": "success"},
        )
    except Exception as error:
        return templates.TemplateResponse(
            request,
            "partials/_simple_message.html",
            {"message": str(error), "level": "error"},
        )


@router.post("/partials/record-score", response_class=HTMLResponse)
def record_score_partial(
    request: Request,
    game_id: str = Form(...),
    home_score: int = Form(...),
    away_score: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        record_game_result(
            db,
            game_id=game_id,
            home_score=home_score,
            away_score=away_score,
        )
        return templates.TemplateResponse(
            request,
            "partials/_simple_message.html",
            {"message": f"Game settled: {home_score}–{away_score}", "level": "success"},
        )
    except Exception as error:
        return templates.TemplateResponse(
            request,
            "partials/_simple_message.html",
            {"message": str(error), "level": "error"},
        )


# --- HTMX Partials: Ingestion Monitoring ---


@router.get("/partials/run-history", response_class=HTMLResponse)
def run_history_partial(
    request: Request,
    db: Session = Depends(get_db),
):
    from edgebook.ingestion.services import list_runs

    runs, _ = list_runs(db, limit=20, offset=0)
    return templates.TemplateResponse(
        request,
        "partials/run_history.html",
        {"runs": runs},
    )


@router.get("/partials/conflict-list", response_class=HTMLResponse)
def conflict_list_partial(
    request: Request,
    db: Session = Depends(get_db),
):
    from edgebook.ingestion.services import list_conflicts

    conflicts = list_conflicts(db)
    conflict_data = [
        {
            "game_id": g.id,
            "home_team": g.home_team.name if g.home_team else "Unknown",
            "away_team": g.away_team.name if g.away_team else "Unknown",
            "scheduled_at": g.scheduled_at.isoformat(),
            "score_sync_state": g.score_sync_state,
        }
        for g in conflicts
    ]
    return templates.TemplateResponse(
        request,
        "partials/conflict_list.html",
        {"conflicts": conflict_data},
    )
