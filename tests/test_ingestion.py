"""Contract coverage for multi-provider ingestion and score handling."""

import json
from datetime import UTC, datetime

from sqlalchemy import func, select

from edgebook.application.operations import (
    resolve_score_conflict,
    settle_confirmed_games,
)
from edgebook.cfb.models import (
    Game,
    GameStatus,
    MarketQuote,
    MarketSelection,
    MarketType,
    ScoreResolution,
    ScoreSyncState,
)
from edgebook.ingestion.adapters import (
    ExternalGame,
    ExternalQuote,
    ExternalScore,
    FixtureProviderAdapter,
    load_normalized_feed,
)
from edgebook.ingestion.models import IngestionRun, ProviderObservation
from edgebook.ingestion.services import sync_games, sync_quotes, sync_scores


def _adapter(
    name: str, *, score: tuple[int, int] = (21, 17), odds: int = -110
) -> FixtureProviderAdapter:
    scheduled_at = datetime(2026, 9, 5, 19, 30, tzinfo=UTC)
    observed_at = datetime(2026, 9, 6, 1, tzinfo=UTC)
    return FixtureProviderAdapter(
        name=name,
        game_records=[ExternalGame("game-1", "Home State", "Away Tech", scheduled_at)],
        quote_records=[
            ExternalQuote(
                "home-quote",
                "game-1",
                MarketType.MONEYLINE,
                None,
                MarketSelection.HOME,
                odds,
                observed_at,
            ),
            ExternalQuote(
                "away-quote",
                "game-1",
                MarketType.MONEYLINE,
                None,
                MarketSelection.AWAY,
                -110,
                observed_at,
            ),
        ],
        score_records=[ExternalScore("final-1", "game-1", *score, observed_at)],
    )


def test_multi_provider_observations_are_idempotent_and_conflicts_hold(db_session):
    """Every provider quote is retained while conflicting scores prevent settlement."""
    source_a = _adapter("source-a", odds=-110)
    source_b = _adapter("source-b", odds=125)
    source_c = _adapter("source-c", score=(17, 21), odds=140)

    assert sync_games(db_session, source_a)["created"] == 1
    assert sync_games(db_session, source_b)["created"] == 1
    assert sync_games(db_session, source_c)["created"] == 1
    assert sync_games(db_session, source_a)["skipped"] == 1
    assert db_session.scalar(select(func.count()).select_from(Game)) == 1

    assert sync_quotes(db_session, source_a)["created"] == 2
    assert sync_quotes(db_session, source_b)["created"] == 2
    assert sync_quotes(db_session, source_c)["created"] == 2
    assert sync_quotes(db_session, source_a)["skipped"] == 2
    assert db_session.scalar(select(func.count()).select_from(MarketQuote)) == 6

    sync_scores(db_session, source_a)
    sync_scores(db_session, source_b)
    conflict = sync_scores(db_session, source_c)
    game = db_session.scalar(select(Game))
    assert game is not None
    assert game.score_sync_state == ScoreSyncState.CONFLICTED.value
    assert conflict["conflicts"] == 1
    assert settle_confirmed_games(db_session) == 0
    assert game.status == GameStatus.SCHEDULED.value

    resolution = resolve_score_conflict(
        db_session,
        game_id=game.id,
        home_score=21,
        away_score=17,
        reason="Verified official result",
        resolved_by="local-operator",
    )
    assert resolution.game_id == game.id
    assert game.status == GameStatus.FINAL.value
    assert game.score_sync_state == ScoreSyncState.RESOLVED.value
    assert db_session.scalar(select(func.count()).select_from(ScoreResolution)) == 1
    assert (
        db_session.scalar(select(func.count()).select_from(ProviderObservation)) == 12
    )
    assert db_session.scalar(select(func.count()).select_from(IngestionRun)) == 11


def test_confirmed_scores_settle_and_normalized_feeds_load(db_session, tmp_path):
    """Two matching providers confirm a score and the scheduler feed is parseable."""
    source_a = _adapter("source-a")
    source_b = _adapter("source-b")
    for adapter in (source_a, source_b):
        sync_games(db_session, adapter)
        sync_scores(db_session, adapter)
    assert settle_confirmed_games(db_session) == 1
    assert db_session.scalar(select(Game)).status == GameStatus.FINAL.value

    feed = tmp_path / "source.json"
    feed.write_text(
        json.dumps(
            {
                "games": [
                    {
                        "external_id": "g2",
                        "home_team": "One",
                        "away_team": "Two",
                        "scheduled_at": "2026-09-06T19:30:00+00:00",
                    }
                ]
            }
        )
    )
    loaded = load_normalized_feed(feed, "source-d")
    assert loaded.games()[0].external_id == "g2"
    assert loaded.quotes() == []
