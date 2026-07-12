"""Coverage for the production pregame odds operations boundary."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from edgebook.cfb.models import Game, MarketSelection, MarketType
from edgebook.ingestion.adapters import (
    ExternalGame,
    ExternalQuote,
    FixtureProviderAdapter,
)
from edgebook.ingestion.models import (
    BackfillCheckpoint,
    IngestionRun,
    ProviderEventLink,
)
from edgebook.ingestion.services import (
    IngestionLockedError,
    begin_backfill_checkpoint,
    complete_backfill_checkpoint,
    fail_backfill_checkpoint,
    ingestion_lock,
    sync_games,
    sync_quotes,
)


def _odds_adapter(
    *, scheduled_at: datetime, observed_at: datetime, home_odds: int
) -> FixtureProviderAdapter:
    return FixtureProviderAdapter(
        name="the-odds-api",
        game_records=[ExternalGame("event-1", "Home State", "Away Tech", scheduled_at)],
        quote_records=[
            ExternalQuote(
                "home-quote",
                "event-1",
                MarketType.MONEYLINE,
                None,
                MarketSelection.HOME,
                home_odds,
                observed_at,
                "the-odds-api:draftkings",
            ),
            ExternalQuote(
                "away-quote",
                "event-1",
                MarketType.MONEYLINE,
                None,
                MarketSelection.AWAY,
                -110,
                observed_at,
                "the-odds-api:draftkings",
            ),
        ],
        score_records=[],
    )


def test_provider_event_link_survives_schedule_change(db_session):
    """A provider event keeps one canonical game when its kickoff changes."""
    initial = _odds_adapter(
        scheduled_at=datetime(2026, 9, 5, 19, 30, tzinfo=UTC),
        observed_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
        home_odds=-120,
    )
    moved = _odds_adapter(
        scheduled_at=datetime(2026, 9, 5, 20, 0, tzinfo=UTC),
        observed_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
        home_odds=-115,
    )

    sync_games(db_session, initial)
    sync_games(db_session, moved)

    link = db_session.scalar(select(ProviderEventLink))
    game = db_session.scalar(select(Game))
    assert link is not None
    assert game is not None
    assert link.game_id == game.id
    assert game.scheduled_at.isoformat() == "2026-09-05T20:00:00"


def test_backfill_checkpoints_resume_and_record_failure(db_session):
    """Completed snapshots skip safely while failures remain resumable."""
    requested_at = datetime(2020, 6, 6, 12, tzinfo=UTC)
    checkpoint = begin_backfill_checkpoint(
        db_session,
        provider="the-odds-api",
        sport="americanfootball_ncaaf",
        markets="h2h,spreads,totals",
        bookmakers="draftkings,fanduel,betmgm,caesars",
        requested_snapshot_at=requested_at,
    )
    assert checkpoint is not None
    complete_backfill_checkpoint(db_session, checkpoint, run_id=None)
    assert (
        begin_backfill_checkpoint(
            db_session,
            provider="the-odds-api",
            sport="americanfootball_ncaaf",
            markets="h2h,spreads,totals",
            bookmakers="draftkings,fanduel,betmgm,caesars",
            requested_snapshot_at=requested_at,
        )
        is None
    )

    failed = begin_backfill_checkpoint(
        db_session,
        provider="the-odds-api",
        sport="americanfootball_ncaaf",
        markets="h2h,spreads,totals",
        bookmakers="draftkings,fanduel,betmgm,caesars",
        requested_snapshot_at=datetime(2020, 6, 7, 12, tzinfo=UTC),
    )
    assert failed is not None
    fail_backfill_checkpoint(db_session, failed, RuntimeError("provider unavailable"))
    persisted = db_session.get(BackfillCheckpoint, failed.id)
    assert persisted is not None
    assert persisted.status == "FAILED"
    assert "provider unavailable" in persisted.error_message


def test_odds_history_api_filters_chronological_bookmaker_observations(
    client, db_session
):
    """The read endpoint exposes source-specific immutable line movement."""
    first = _odds_adapter(
        scheduled_at=datetime(2026, 9, 5, 19, 30, tzinfo=UTC),
        observed_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
        home_odds=-120,
    )
    second = _odds_adapter(
        scheduled_at=datetime(2026, 9, 5, 19, 30, tzinfo=UTC),
        observed_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
        home_odds=-115,
    )
    sync_games(db_session, first)
    sync_quotes(db_session, first)
    sync_games(db_session, second)
    sync_quotes(db_session, second)
    game = db_session.scalar(select(Game))
    assert game is not None

    response = client.get(
        f"/cfb/games/{game.id}/odds-history",
        params={
            "source": "the-odds-api:draftkings",
            "market_type": "MONEYLINE",
            "selection": "HOME",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert [item["american_odds"] for item in payload] == [-120, -115]
    assert [item["source_event_id"] for item in payload] == ["event-1", "event-1"]
    assert payload[0]["observed_at"] < payload[1]["observed_at"]


def test_postgres_lock_rejects_overlapping_ingestion_job():
    """The production advisory lock refuses a concurrent scheduler invocation."""
    db = SimpleNamespace(
        bind=SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
        scalar=lambda *args, **kwargs: False,
    )
    with pytest.raises(IngestionLockedError, match="already running"):
        with ingestion_lock(db):
            pass


def test_run_records_provider_quota_metadata(db_session):
    """Provider request metadata remains available for quota observability."""
    adapter = _odds_adapter(
        scheduled_at=datetime(2026, 9, 5, 19, 30, tzinfo=UTC),
        observed_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
        home_odds=-120,
    )
    adapter.quota_used = 30
    adapter.quota_remaining = 99_970
    sync_games(
        db_session, adapter, requested_snapshot_at=adapter.quotes()[0].observed_at
    )
    run = db_session.scalar(select(IngestionRun))
    assert run is not None
    assert run.quota_used == 30
    assert run.quota_remaining == 99_970
