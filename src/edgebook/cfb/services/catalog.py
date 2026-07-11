"""Manual college-football intake operations, catalog sub-module."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from edgebook.cfb.models import Game, GameStatus, Market, SportType, Team


class CfbError(Exception):
    """Base exception for expected CFB domain operation failures."""


class CfbNotFoundError(CfbError):
    """Raised when a requested CFB resource cannot be found."""


class CfbConflictError(CfbError):
    """Raised when a CFB operation conflicts with stored state."""


class CfbValidationError(CfbError):
    """Raised when CFB domain validation fails."""


def normalize_team_name(name: str) -> str:
    """Collapse whitespace and normalize a team name for uniqueness checks."""
    return " ".join(name.strip().split()).lower()


def create_team(db: Session, *, name: str) -> Team:
    """Create a reusable manually-entered team."""
    display_name = " ".join(name.strip().split())
    normalized_name = normalize_team_name(display_name)
    if (
        db.scalar(select(Team).where(Team.normalized_name == normalized_name))
        is not None
    ):
        raise CfbConflictError("A team with that name already exists")
    try:
        team = Team(name=display_name, normalized_name=normalized_name)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team
    except Exception:
        db.rollback()
        raise


def create_game(
    db: Session,
    *,
    home_team_id: str,
    away_team_id: str,
    scheduled_at: datetime,
    sport: SportType = SportType.CFB,
) -> Game:
    """Create a scheduled game after validating both teams."""
    if home_team_id == away_team_id:
        raise CfbValidationError("Home and away teams must be distinct")
    home_team = db.get(Team, home_team_id)
    away_team = db.get(Team, away_team_id)
    if home_team is None or away_team is None:
        raise CfbNotFoundError("Home and away teams must both exist")
    if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
        raise CfbValidationError("Scheduled time must include a timezone")
    try:
        game = Game(
            sport=sport,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            scheduled_at=scheduled_at.astimezone(UTC),
            status=GameStatus.SCHEDULED,
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        return game
    except Exception:
        db.rollback()
        raise


def list_games(
    db: Session,
    *,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Game], int]:
    """Return paginated games newest-first with teams and markets eager-loaded."""
    query = (
        select(Game)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
            selectinload(Game.markets).selectinload(Market.quotes),
        )
        .order_by(Game.scheduled_at.desc())
    )
    if status is not None:
        query = query.where(Game.status == status)

    count_q = select(func.count()).select_from(Game)
    if status is not None:
        count_q = count_q.where(Game.status == status)
    total = db.scalar(count_q) or 0

    games = db.scalars(query.limit(limit).offset(offset)).unique().all()
    return list(games), total


def get_game(db: Session, game_id: str) -> Game:
    """Return a game with the teams, markets, and quotes needed by its detail view."""
    game = db.scalar(
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
            selectinload(Game.markets).selectinload(Market.quotes),
        )
    )
    if game is None:
        raise CfbNotFoundError(f"Game {game_id} was not found")
    return game
