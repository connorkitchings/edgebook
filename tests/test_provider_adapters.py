"""Contract tests for recurring and historical odds provider mappings."""

from datetime import UTC, datetime

import pytest

from edgebook.cfb.models import MarketSelection, MarketType
from edgebook.ingestion.adapters import (
    CollegeFootballDataAdapter,
    ProviderConfigurationError,
    SportsDataIoAdapter,
    TheOddsApiAdapter,
)
from edgebook.ingestion.services import sync_games, sync_quotes

ODDS_PAYLOAD = [
    {
        "id": "event-1",
        "commence_time": "2026-09-05T19:30:00Z",
        "home_team": "Home State",
        "away_team": "Away Tech",
        "bookmakers": [
            {
                "key": "draftkings",
                "last_update": "2026-09-04T10:00:00Z",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Home State", "price": -135},
                            {"name": "Away Tech", "price": 115},
                        ],
                    },
                    {
                        "key": "spreads",
                        "outcomes": [
                            {"name": "Home State", "price": -110, "point": -3.5},
                            {"name": "Away Tech", "price": -110, "point": 3.5},
                        ],
                    },
                    {
                        "key": "totals",
                        "outcomes": [
                            {"name": "Over", "price": -105, "point": 48.5},
                            {"name": "Under", "price": -115, "point": 48.5},
                        ],
                    },
                ],
            },
            {
                "key": "fanduel",
                "last_update": "2026-09-04T10:00:00Z",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Home State", "price": -130},
                            {"name": "Away Tech", "price": 110},
                        ],
                    }
                ],
            },
        ],
    }
]


def test_odds_api_maps_bookmakers_and_all_supported_markets(db_session):
    adapter = TheOddsApiAdapter("", payload=ODDS_PAYLOAD)

    quotes = adapter.quotes()
    assert len(quotes) == 8
    assert {quote.source for quote in quotes} == {
        "the-odds-api:draftkings",
        "the-odds-api:fanduel",
    }
    assert (MarketType.SPREAD, -3500, MarketSelection.HOME) in {
        (quote.market_type, quote.line_millipoints, quote.selection) for quote in quotes
    }
    assert (MarketType.TOTAL, 48500, MarketSelection.UNDER) in {
        (quote.market_type, quote.line_millipoints, quote.selection) for quote in quotes
    }

    assert sync_games(db_session, adapter)["created"] == 1
    assert sync_quotes(db_session, adapter)["created"] == 8
    assert sync_quotes(db_session, adapter)["skipped"] == 8


def test_odds_api_requires_key_for_live_calls():
    with pytest.raises(ProviderConfigurationError, match="ODDS_API_KEY"):
        TheOddsApiAdapter("")


def test_college_football_data_fixture_mapping_keeps_provider_source():
    adapter = CollegeFootballDataAdapter.from_payload(
        [
            {
                "id": 44,
                "home_team": "Home State",
                "away_team": "Away Tech",
                "start_date": "2026-09-05T19:30:00Z",
            }
        ],
        [
            {
                "id": 44,
                "provider": "DraftKings",
                "home_moneyline": -130,
                "away_moneyline": 110,
                "home_spread": -110,
                "away_spread": -110,
                "spread": -3.5,
            }
        ],
    )
    assert adapter.games()[0].scheduled_at == datetime(2026, 9, 5, 19, 30, tzinfo=UTC)
    assert {quote.source for quote in adapter.quotes()} == {
        "college-football-data:draftkings"
    }
    assert any(
        quote.selection == MarketSelection.AWAY and quote.line_millipoints == 3500
        for quote in adapter.quotes()
    )


def test_sportsdataio_fixture_mapping_preserves_book_and_line_movement():
    adapter = SportsDataIoAdapter.from_payload(
        [
            {
                "GameID": 81,
                "HomeTeamName": "Home State",
                "AwayTeamName": "Away Tech",
                "DateTime": "2026-09-05T19:30:00Z",
            }
        ],
        [
            {
                "GameID": 81,
                "Sportsbook": "DraftKings",
                "LastUpdated": "2026-09-04T10:00:00Z",
                "HomeMoneyLine": -135,
                "AwayMoneyLine": 115,
                "PointSpread": -3.5,
                "HomePointSpreadPayout": -110,
                "AwayPointSpreadPayout": -110,
                "OverUnder": 48.5,
                "OverPayout": -105,
                "UnderPayout": -115,
            }
        ],
    )
    assert len(adapter.quotes()) == 6
    assert {quote.source for quote in adapter.quotes()} == {"sportsdataio:DraftKings"}
    assert any(
        quote.selection == MarketSelection.UNDER and quote.line_millipoints == 48500
        for quote in adapter.quotes()
    )
