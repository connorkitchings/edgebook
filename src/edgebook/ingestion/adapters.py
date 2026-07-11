"""Provider-neutral normalized feed contracts and deterministic fixture adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from edgebook.cfb.models import MarketSelection, MarketType


@dataclass(frozen=True)
class ExternalGame:
    external_id: str
    home_team: str
    away_team: str
    scheduled_at: datetime


@dataclass(frozen=True)
class ExternalQuote:
    external_id: str
    game_external_id: str
    market_type: MarketType
    line_millipoints: int | None
    selection: MarketSelection
    american_odds: int
    observed_at: datetime


@dataclass(frozen=True)
class ExternalScore:
    external_id: str
    game_external_id: str
    home_score: int
    away_score: int
    observed_at: datetime


class ProviderAdapter(Protocol):
    """Normalized provider contract; concrete vendors map their feeds here."""

    name: str

    def games(self) -> list[ExternalGame]: ...

    def quotes(self) -> list[ExternalQuote]: ...

    def scores(self) -> list[ExternalScore]: ...


@dataclass
class FixtureProviderAdapter:
    """In-memory adapter used for contract tests and scheduler dry runs."""

    name: str
    game_records: list[ExternalGame]
    quote_records: list[ExternalQuote]
    score_records: list[ExternalScore]

    def games(self) -> list[ExternalGame]:
        return self.game_records

    def quotes(self) -> list[ExternalQuote]:
        return self.quote_records

    def scores(self) -> list[ExternalScore]:
        return self.score_records


def load_normalized_feed(path: Path, provider: str) -> FixtureProviderAdapter:
    """Load a normalized provider feed for local syncs and scheduler hooks."""
    payload = json.loads(path.read_text())
    return FixtureProviderAdapter(
        name=provider,
        game_records=[
            ExternalGame(
                external_id=record["external_id"],
                home_team=record["home_team"],
                away_team=record["away_team"],
                scheduled_at=datetime.fromisoformat(record["scheduled_at"]),
            )
            for record in payload.get("games", [])
        ],
        quote_records=[
            ExternalQuote(
                external_id=record["external_id"],
                game_external_id=record["game_external_id"],
                market_type=MarketType(record["market_type"]),
                line_millipoints=record.get("line_millipoints"),
                selection=MarketSelection(record["selection"]),
                american_odds=record["american_odds"],
                observed_at=datetime.fromisoformat(record["observed_at"]),
            )
            for record in payload.get("quotes", [])
        ],
        score_records=[
            ExternalScore(
                external_id=record["external_id"],
                game_external_id=record["game_external_id"],
                home_score=record["home_score"],
                away_score=record["away_score"],
                observed_at=datetime.fromisoformat(record["observed_at"]),
            )
            for record in payload.get("scores", [])
        ],
    )
