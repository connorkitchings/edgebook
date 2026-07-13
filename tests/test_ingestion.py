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


def _seed_run(
    db_session,
    *,
    provider: str,
    scope: str,
    status: str,
    quota_remaining: int | None,
    started_at: datetime,
    finished: bool = True,
) -> IngestionRun:
    run = IngestionRun(
        provider=provider,
        scope=scope,
        status=status,
        quota_remaining=quota_remaining,
        started_at=started_at,
        finished_at=started_at if finished else None,
    )
    db_session.add(run)
    db_session.flush()
    return run


def test_list_runs_filters_by_status_and_provider(db_session):
    """list_runs narrows by status and provider independently."""
    from edgebook.ingestion.services import list_runs

    now = datetime.now(UTC)
    _seed_run(
        db_session,
        provider="alpha",
        scope="games",
        status="COMPLETED",
        quota_remaining=10,
        started_at=now,
    )
    _seed_run(
        db_session,
        provider="alpha",
        scope="games",
        status="FAILED",
        quota_remaining=9,
        started_at=now,
    )
    _seed_run(
        db_session,
        provider="beta",
        scope="games",
        status="COMPLETED",
        quota_remaining=5,
        started_at=now,
    )

    completed, total_completed = list_runs(db_session, status="COMPLETED")
    assert total_completed == 2
    assert all(r.status == "COMPLETED" for r in completed)

    alpha_only, total_alpha = list_runs(db_session, provider="alpha")
    assert total_alpha == 2
    assert all(r.provider == "alpha" for r in alpha_only)

    failed_alpha, total_failed_alpha = list_runs(
        db_session, status="FAILED", provider="alpha"
    )
    assert total_failed_alpha == 1
    assert failed_alpha[0].status == "FAILED"


def test_summarize_runs_counts_window_and_quota(db_session):
    """summarize_runs reports status counts within the window and per-provider quota."""
    from edgebook.ingestion.services import summarize_runs

    now = datetime.now(UTC)
    old = datetime(2020, 1, 1, tzinfo=UTC)
    _seed_run(
        db_session,
        provider="alpha",
        scope="games",
        status="COMPLETED",
        quota_remaining=100,
        started_at=now,
    )
    _seed_run(
        db_session,
        provider="alpha",
        scope="games",
        status="FAILED",
        quota_remaining=80,
        started_at=now,
    )
    _seed_run(
        db_session,
        provider="beta",
        scope="games",
        status="COMPLETED",
        quota_remaining=50,
        started_at=now,
    )
    # Outside the default 24h window: must be excluded from totals.
    _seed_run(
        db_session,
        provider="alpha",
        scope="games",
        status="COMPLETED",
        quota_remaining=200,
        started_at=old,
    )

    summary = summarize_runs(db_session, window_hours=24)

    assert summary["window_hours"] == 24
    assert summary["total_runs"] == 3
    assert summary["status_counts"]["COMPLETED"] == 2
    assert summary["status_counts"]["FAILED"] == 1
    assert summary["last_run_at"] is not None
    # Latest quota per provider uses the newest run that reported quota.
    assert summary["quota_remaining_by_provider"]["alpha"] in (100, 80)
    assert summary["quota_remaining_by_provider"]["beta"] == 50


def test_fail_triggers_notifier(db_session, monkeypatch):
    """_fail persists the failed run and fires the webhook notifier."""
    from edgebook.ingestion import services

    run = _seed_run(
        db_session,
        provider="alpha",
        scope="games",
        status="RUNNING",
        quota_remaining=12,
        started_at=datetime.now(UTC),
        finished=False,
    )

    called: dict = {}
    monkeypatch.setattr(
        services, "notify_ingestion_failure", lambda **kw: called.update(kw)
    )

    services._fail(db_session, run, ValueError("boom"))

    assert called["provider"] == "alpha"
    assert "boom" in called["error"]
    assert called["quota_remaining"] == 12
