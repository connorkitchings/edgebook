"""Idempotent persistence and settlement coordination for normalized providers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from edgebook.cfb.models import (
    Game,
    GameStatus,
    Market,
    MarketQuote,
    MarketStatus,
    ScoreObservation,
    ScoreResolution,
    ScoreSyncState,
    Team,
)
from edgebook.cfb.services import EXPECTED_SELECTIONS, normalize_team_name
from edgebook.ingestion.adapters import ProviderAdapter
from edgebook.ingestion.models import IngestionRun, ProviderObservation
from edgebook.wagering.services import record_game_result


class IngestionError(Exception):
    """Base exception for expected provider-sync errors."""


class IngestionNotFoundError(IngestionError):
    pass


class IngestionConflictError(IngestionError):
    pass


def _payload_hash(payload: dict) -> tuple[str, str]:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def _run(db: Session, provider: str, scope: str) -> IngestionRun:
    run = IngestionRun(provider=provider, scope=scope, status="RUNNING")
    db.add(run)
    db.flush()
    return run


def _finish(db: Session, run: IngestionRun, status: str = "COMPLETED") -> dict:
    run.status = status
    run.finished_at = datetime.now(UTC)
    db.commit()
    return {
        "run_id": run.id,
        "status": run.status,
        "seen": run.records_seen,
        "created": run.records_created,
        "skipped": run.records_skipped,
        "conflicts": run.conflict_count,
    }


def _existing_observation(
    db: Session, provider: str, scope: str, external_id: str, payload_hash: str
) -> ProviderObservation | None:
    return db.scalar(
        select(ProviderObservation).where(
            ProviderObservation.provider == provider,
            ProviderObservation.scope == scope,
            ProviderObservation.external_id == external_id,
            ProviderObservation.payload_hash == payload_hash,
        )
    )


def _remember(
    db: Session,
    *,
    run: IngestionRun,
    external_id: str,
    payload: dict,
    game_id: str | None,
) -> bool:
    raw, digest = _payload_hash(payload)
    if _existing_observation(db, run.provider, run.scope, external_id, digest):
        run.records_skipped += 1
        return False
    db.add(
        ProviderObservation(
            run_id=run.id,
            provider=run.provider,
            scope=run.scope,
            external_id=external_id,
            payload_hash=digest,
            game_id=game_id,
            payload=raw,
        )
    )
    run.records_created += 1
    return True


def _team(db: Session, name: str) -> Team:
    normalized = normalize_team_name(name)
    team = db.scalar(select(Team).where(Team.normalized_name == normalized))
    if team is None:
        team = Team(name=" ".join(name.split()), normalized_name=normalized)
        db.add(team)
        db.flush()
    return team


def _game_for_external_id(db: Session, provider: str, external_id: str) -> Game | None:
    game_id = db.scalar(
        select(ProviderObservation.game_id)
        .where(
            ProviderObservation.provider == provider,
            ProviderObservation.scope == "GAMES",
            ProviderObservation.external_id == external_id,
            ProviderObservation.game_id.is_not(None),
        )
        .order_by(ProviderObservation.observed_at.desc())
    )
    return db.get(Game, game_id) if game_id else None


def sync_games(db: Session, adapter: ProviderAdapter) -> dict:
    """Persist games and schedule changes without duplicating provider observations."""
    run = _run(db, adapter.name, "GAMES")
    try:
        for record in adapter.games():
            run.records_seen += 1
            payload = {
                "home_team": record.home_team,
                "away_team": record.away_team,
                "scheduled_at": record.scheduled_at.isoformat(),
            }
            raw, digest = _payload_hash(payload)
            if _existing_observation(
                db, adapter.name, "GAMES", record.external_id, digest
            ):
                run.records_skipped += 1
                continue
            game = _game_for_external_id(db, adapter.name, record.external_id)
            home = _team(db, record.home_team)
            away = _team(db, record.away_team)
            if game is None:
                if home.id == away.id:
                    raise IngestionConflictError("Provider game has identical teams")
                game = db.scalar(
                    select(Game).where(
                        Game.home_team_id == home.id,
                        Game.away_team_id == away.id,
                        Game.scheduled_at == record.scheduled_at.astimezone(UTC),
                    )
                )
                if game is None:
                    game = Game(
                        home_team_id=home.id,
                        away_team_id=away.id,
                        scheduled_at=record.scheduled_at.astimezone(UTC),
                        status=GameStatus.SCHEDULED.value,
                    )
                    db.add(game)
                    db.flush()
            elif game.status == GameStatus.SCHEDULED.value:
                game.scheduled_at = record.scheduled_at.astimezone(UTC)
            _remember(
                db,
                run=run,
                external_id=record.external_id,
                payload=payload,
                game_id=game.id,
            )
        return _finish(db, run)
    except Exception as error:
        db.rollback()
        raise IngestionError(str(error)) from error


def sync_quotes(db: Session, adapter: ProviderAdapter) -> dict:
    """Persist every source quote observation; no provider value is overwritten."""
    run = _run(db, adapter.name, "ODDS")
    try:
        for record in adapter.quotes():
            run.records_seen += 1
            game = _game_for_external_id(db, adapter.name, record.game_external_id)
            if game is None:
                raise IngestionNotFoundError(
                    f"No imported game for {adapter.name}:{record.game_external_id}"
                )
            payload = {
                "game_external_id": record.game_external_id,
                "market_type": record.market_type.value,
                "line_millipoints": record.line_millipoints,
                "selection": record.selection.value,
                "american_odds": record.american_odds,
                "observed_at": record.observed_at.isoformat(),
            }
            raw, digest = _payload_hash(payload)
            if _existing_observation(
                db, adapter.name, "ODDS", record.external_id, digest
            ):
                run.records_skipped += 1
                continue
            market = db.scalar(
                select(Market).where(
                    Market.game_id == game.id,
                    Market.market_type == record.market_type.value,
                    Market.line_millipoints == record.line_millipoints,
                )
            )
            if market is None:
                market = Market(
                    game_id=game.id,
                    market_type=record.market_type.value,
                    line_millipoints=record.line_millipoints,
                    status=MarketStatus.DRAFT.value,
                )
                db.add(market)
                db.flush()
            quote = MarketQuote(
                market_id=market.id,
                selection=record.selection.value,
                american_odds=record.american_odds,
                source=adapter.name,
                source_quote_id=f"{record.external_id}:{digest[:12]}",
                observed_at=record.observed_at.astimezone(UTC),
            )
            db.add(quote)
            selections = set(
                db.scalars(
                    select(MarketQuote.selection).where(
                        MarketQuote.market_id == market.id
                    )
                )
            ) | {record.selection.value}
            if EXPECTED_SELECTIONS[record.market_type].issubset(
                {type(record.selection)(value) for value in selections}
            ):
                market.status = MarketStatus.OPEN
            _remember(
                db,
                run=run,
                external_id=record.external_id,
                payload=payload,
                game_id=game.id,
            )
        return _finish(db, run)
    except Exception as error:
        db.rollback()
        raise IngestionError(str(error)) from error


def sync_scores(db: Session, adapter: ProviderAdapter) -> dict:
    """Persist score observations and hold games where sources disagree."""
    run = _run(db, adapter.name, "SCORES")
    try:
        touched_games: set[str] = set()
        for record in adapter.scores():
            run.records_seen += 1
            game = _game_for_external_id(db, adapter.name, record.game_external_id)
            if game is None:
                raise IngestionNotFoundError(
                    f"No imported game for {adapter.name}:{record.game_external_id}"
                )
            payload = {
                "game_external_id": record.game_external_id,
                "home_score": record.home_score,
                "away_score": record.away_score,
                "observed_at": record.observed_at.isoformat(),
            }
            if _remember(
                db,
                run=run,
                external_id=record.external_id,
                payload=payload,
                game_id=game.id,
            ):
                db.add(
                    ScoreObservation(
                        game_id=game.id,
                        source=adapter.name,
                        source_event_id=record.external_id,
                        home_score=record.home_score,
                        away_score=record.away_score,
                        observed_at=record.observed_at.astimezone(UTC),
                        payload=json.dumps(payload, sort_keys=True),
                    )
                )
                touched_games.add(game.id)
        db.flush()
        for game_id in touched_games:
            game = db.get(Game, game_id)
            if game is None:
                raise IngestionNotFoundError(f"Game {game_id} disappeared during sync")
            pairs = set(
                db.execute(
                    select(
                        ScoreObservation.home_score, ScoreObservation.away_score
                    ).where(ScoreObservation.game_id == game_id)
                ).all()
            )
            source_count = int(
                db.scalar(
                    select(func.count(func.distinct(ScoreObservation.source))).where(
                        ScoreObservation.game_id == game_id
                    )
                )
                or 0
            )
            if len(pairs) > 1:
                game.score_sync_state = ScoreSyncState.CONFLICTED.value
                run.conflict_count += 1
            elif source_count >= 2:
                game.score_sync_state = ScoreSyncState.CONFIRMED.value
            else:
                game.score_sync_state = ScoreSyncState.UNCONFIRMED.value
        return _finish(db, run)
    except Exception as error:
        db.rollback()
        raise IngestionError(str(error)) from error


def settle_confirmed_games(db: Session) -> int:
    """Settle only provider-confirmed games that are not already final."""
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
    """Record a local operator decision and settle a held game atomically."""
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
