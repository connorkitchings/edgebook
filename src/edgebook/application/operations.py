"""Cross-domain workflows invoked by APIs and scheduler commands."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from edgebook.cfb.models import (
    Game,
    GameStatus,
    ScoreObservation,
    ScoreResolution,
    ScoreSyncState,
)
from edgebook.ingestion.services import IngestionConflictError, IngestionNotFoundError
from edgebook.wagering.models import BetReview
from edgebook.wagering.reviews import (
    claim_pending_reviews as claim_pending_review_tasks,
)
from edgebook.wagering.services import record_game_result


def settle_confirmed_games(db: Session) -> int:
    """Settle only games independently confirmed by external score sources."""
    games = list(
        db.scalars(
            select(Game).where(
                Game.status == GameStatus.SCHEDULED.value,
                Game.score_sync_state == ScoreSyncState.CONFIRMED.value,
            )
        )
    )
    settled = 0
    for game in games:
        observation = db.scalar(
            select(ScoreObservation)
            .where(ScoreObservation.game_id == game.id)
            .order_by(ScoreObservation.observed_at.desc())
        )
        if observation is None:
            continue
        record_game_result(
            db,
            game_id=game.id,
            home_score=observation.home_score,
            away_score=observation.away_score,
        )
        settled += 1
    return settled


def resolve_score_conflict(
    db: Session,
    *,
    game_id: str,
    home_score: int,
    away_score: int,
    reason: str,
    resolved_by: str,
) -> ScoreResolution:
    """Record an operator score decision and settle its wagers atomically."""
    game = db.get(Game, game_id)
    if game is None:
        raise IngestionNotFoundError(f"Game {game_id} was not found")
    if game.status != GameStatus.SCHEDULED.value:
        raise IngestionConflictError("Only scheduled games can be resolved")
    if game.score_sync_state != ScoreSyncState.CONFLICTED.value:
        raise IngestionConflictError("Only conflicted games require score resolution")
    if not reason.strip() or not resolved_by.strip():
        raise IngestionConflictError("Reason and resolver are required")
    try:
        record_game_result(
            db,
            game_id=game_id,
            home_score=home_score,
            away_score=away_score,
            commit=False,
        )
        game.score_sync_state = ScoreSyncState.RESOLVED.value
        resolution = ScoreResolution(
            game_id=game_id,
            home_score=home_score,
            away_score=away_score,
            reason=reason.strip(),
            resolved_by=resolved_by.strip(),
        )
        db.add(resolution)
        db.commit()
        db.refresh(resolution)
        return resolution
    except Exception:
        db.rollback()
        raise


def claim_pending_reviews(db: Session, *, limit: int = 50) -> list[BetReview]:
    """Claim review work through the application scheduling boundary."""
    return claim_pending_review_tasks(db, limit=limit)
